"""
Base Agent class for multi-agent system
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.communication.message import (
    Message,
    MessageType,
    TaskRequest,
    TaskResult,
    ValidationRequest,
)
from app.agents.communication.message_bus import MessageBus
from app.tools.collection import ToolCollection

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent"""

    agent_id: str
    agent_type: str
    description: str
    max_concurrent_tasks: int = 3
    task_timeout: float = 60.0
    enable_memory: bool = True


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.

    Each agent:
    - Has a unique ID and type
    - Can execute tasks
    - Can communicate with other agents via message bus
    - Has access to specific tools
    - Uses LLM for reasoning
    """

    def __init__(
        self,
        config: AgentConfig,
        message_bus: MessageBus,
        tools: Optional[ToolCollection] = None,
        llm: Optional[Any] = None,
    ):
        self.config = config
        self.agent_id = config.agent_id
        self.agent_type = config.agent_type
        self.message_bus = message_bus
        self.tools = tools or ToolCollection()
        self.llm = llm  # LLM is optional, agents can use if provided

        # Task management
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_semaphore = asyncio.Semaphore(config.max_concurrent_tasks)

        # Memory
        self.short_term_memory: List[Dict] = []  # Recent interactions
        self.conversation_history: List[Dict] = []

        # Metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "avg_task_duration": 0.0,
        }

        # Register with message bus
        self.message_bus.register_agent(self.agent_id)

        logger.info(f"🤖 Initialized {self.agent_type} agent: {self.agent_id}")

    @abstractmethod
    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """
        Execute a task (must be implemented by subclasses).

        Args:
            task: Task to execute

        Returns:
            TaskResult with outcome
        """
        pass

    async def run(self):
        """
        Main loop: listen for messages and execute tasks.
        """
        logger.info(f"▶️  {self.agent_id} started listening...")

        while True:
            try:
                # Receive next message
                message = await self.message_bus.receive(self.agent_id, timeout=1.0)

                if message:
                    await self._handle_message(message)

            except asyncio.CancelledError:
                logger.info(f"🛑 {self.agent_id} stopping...")
                break
            except Exception as e:
                logger.error(f"❌ Error in {self.agent_id}: {e}")
                self.metrics["tasks_failed"] += 1

    async def _handle_message(self, message: Message):
        """Handle incoming message"""
        self.metrics["messages_received"] += 1

        logger.debug(
            f"📨 {self.agent_id} handling {message.type.value} "
            f"from {message.sender}"
        )

        if message.type == MessageType.TASK_REQUEST:
            await self._handle_task_request(message)

        elif message.type == MessageType.QUERY:
            await self._handle_query(message)

        elif message.type == MessageType.VALIDATION_REQUEST:
            await self._handle_validation_request(message)

        elif message.type == MessageType.NOTIFICATION:
            await self._handle_notification(message)

        elif message.type == MessageType.TASK_RESULT:
            # Task results are typically sent as replies, not new messages
            # We can safely ignore them here as they're handled by request_agent
            logger.debug(f"Received TASK_RESULT message (id: {message.id})")
        else:
            logger.warning(
                f"⚠️  {self.config.agent_id} received unknown message type: {message.type}"
            )

    async def _handle_task_request(self, message: Message):
        """Handle task execution request"""
        async with self.task_semaphore:
            start_time = datetime.now()

            try:
                # Extract task
                task = TaskRequest(**message.content)

                # Execute task
                logger.info(f"🎯 {self.agent_id} executing: {task.description}")
                result = await self.execute_task(task)

                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()
                result.execution_time = duration

                # Update metrics
                self.metrics["tasks_completed"] += 1
                self._update_avg_duration(duration)

                # Send reply
                await self.message_bus.reply(message, content=result.__dict__)

                logger.info(f"✅ {self.agent_id} completed task in {duration:.2f}s")

            except Exception as e:
                logger.error(f"❌ Task execution failed: {e}")
                self.metrics["tasks_failed"] += 1

                # Send error reply
                error_result = TaskResult(
                    task_id=message.id, success=False, error=str(e)
                )

                await self.message_bus.reply(message, content=error_result.__dict__)

    async def _handle_query(self, message: Message):
        """Handle query from another agent"""
        # Subclasses can override to handle specific queries
        await self.message_bus.reply(
            message, content={"answer": "Query not supported by this agent"}
        )

    async def _handle_validation_request(self, message: Message):
        """Handle validation request"""
        # Subclasses can override
        await self.message_bus.reply(
            message, content={"is_valid": True, "confidence": 0.5}
        )

    async def _handle_notification(self, message: Message):
        """Handle notification (pub/sub event)"""
        # Subclasses can override to react to events
        pass

    async def request_agent(
        self, target_agent: str, task: TaskRequest, timeout: Optional[float] = None
    ) -> Optional[TaskResult]:
        """
        Request another agent to execute a task.

        Args:
            target_agent: Agent ID to request
            task: Task to execute
            timeout: Optional timeout

        Returns:
            TaskResult or None if timeout
        """
        timeout = timeout or self.config.task_timeout

        logger.debug(
            f"📤 {self.agent_id} requesting {target_agent}: " f"{task.description}"
        )

        reply = await self.message_bus.request(
            sender=self.agent_id,
            receiver=target_agent,
            content=task.__dict__,
            timeout=timeout,
        )

        self.metrics["messages_sent"] += 1

        if reply:
            return TaskResult(**reply.content)
        return None

    async def query_agent(
        self, target_agent: str, question: str, timeout: float = 10.0
    ) -> Optional[str]:
        """
        Query another agent for information.

        Args:
            target_agent: Agent to query
            question: Question to ask
            timeout: Max wait time

        Returns:
            Answer or None
        """
        message = Message(
            sender=self.agent_id,
            receiver=target_agent,
            type=MessageType.QUERY,
            content={"question": question},
        )

        reply = await self.message_bus.send(message, timeout=timeout)

        if reply:
            return reply.content.get("answer")
        return None

    async def notify(self, topic: str, data: Dict):
        """
        Publish notification to a topic.

        Args:
            topic: Topic name
            data: Notification data
        """
        await self.message_bus.publish(topic=topic, sender=self.agent_id, content=data)

        self.metrics["messages_sent"] += 1

    def subscribe_to(self, topic: str, callback):
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe
            callback: Function to call on notification
        """
        self.message_bus.subscribe(topic, callback)

    def _update_avg_duration(self, new_duration: float):
        """Update average task duration"""
        total = self.metrics["tasks_completed"]
        if total > 0:
            current_avg = self.metrics["avg_task_duration"]
            self.metrics["avg_task_duration"] = (
                current_avg * (total - 1) + new_duration
            ) / total

    def get_metrics(self) -> Dict:
        """Get agent metrics"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            **self.metrics,
        }

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info(f"🛑 Shutting down {self.agent_id}...")

        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()

        self.active_tasks.clear()
