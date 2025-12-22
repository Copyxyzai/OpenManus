"""
Message Bus for inter-agent communication
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from app.agents.communication.message import Message, MessagePriority, MessageType

logger = logging.getLogger(__name__)


class MessageBus:
    """
    Central message bus for agent communication.

    Supports:
    - Direct messaging (agent-to-agent)
    - Publish-subscribe patterns
    - Request-reply with timeout
    - Message prioritization
    """

    def __init__(self):
        # Mailboxes for each agent
        self.mailboxes: Dict[str, asyncio.Queue] = {}

        # Pub/sub subscriptions
        self.subscriptions: Dict[str, List[Callable]] = defaultdict(list)

        # Pending requests awaiting replies
        self.pending_requests: Dict[str, asyncio.Future] = {}

        # Message history for debugging
        self.message_history: List[Message] = []
        self.max_history = 1000

        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "avg_latency": 0.0,
            "errors": 0,
        }

    def register_agent(self, agent_id: str):
        """Register an agent with the bus"""
        if agent_id not in self.mailboxes:
            self.mailboxes[agent_id] = asyncio.Queue()
            logger.info(f"📬 Registered agent: {agent_id}")

    async def send(
        self, message: Message, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Send a message to a specific agent.

        Args:
            message: Message to send
            timeout: Optional timeout for reply

        Returns:
            Reply message if waiting for reply, None otherwise
        """
        # Ensure receiver is registered
        if message.receiver not in self.mailboxes:
            logger.error(f"❌ Unknown receiver: {message.receiver}")
            self.metrics["errors"] += 1
            return None

        # Add to receiver's mailbox
        await self.mailboxes[message.receiver].put(message)

        # Track metrics
        self.metrics["messages_sent"] += 1
        self._add_to_history(message)

        logger.debug(
            f"📨 {message.sender} → {message.receiver}: " f"{message.type.value}"
        )

        # If this is a request, wait for reply
        if timeout is not None:
            return await self._wait_for_reply(message.id, timeout)

        return None

    async def receive(
        self, agent_id: str, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Receive next message from mailbox.

        Args:
            agent_id: Agent ID receiving the message
            timeout: Optional timeout

        Returns:
            Next message or None if timeout
        """
        if agent_id not in self.mailboxes:
            logger.error(f"❌ Unknown agent: {agent_id}")
            return None

        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.mailboxes[agent_id].get(), timeout=timeout
                )
            else:
                message = await self.mailboxes[agent_id].get()

            self.metrics["messages_received"] += 1

            logger.debug(
                f"📥 {agent_id} received: {message.type.value} "
                f"from {message.sender}"
            )

            return message

        except asyncio.TimeoutError:
            return None

    async def request(
        self, sender: str, receiver: str, content: Dict, timeout: float = 30.0
    ) -> Optional[Message]:
        """
        Send a request and wait for reply.

        Args:
            sender: Requesting agent
            receiver: Target agent
            content: Request content
            timeout: Max wait time

        Returns:
            Reply message or None if timeout
        """
        message = Message(
            sender=sender,
            receiver=receiver,
            type=MessageType.TASK_REQUEST,
            content=content,
        )

        # Create future for reply
        future = asyncio.Future()
        self.pending_requests[message.id] = future

        # Send request
        await self.send(message)

        # Wait for reply
        try:
            reply = await asyncio.wait_for(future, timeout=timeout)
            return reply
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Request timeout: {sender} → {receiver}")
            del self.pending_requests[message.id]
            return None

    async def reply(self, original_message: Message, content: Dict):
        """
        Reply to a message.

        Args:
            original_message: Message being replied to
            content: Reply content
        """
        reply_message = Message(
            sender=original_message.receiver,
            receiver=original_message.sender,
            type=MessageType.TASK_RESULT,
            content=content,
            reply_to=original_message.id,
            correlation_id=original_message.correlation_id,
        )

        await self.send(reply_message)

        # Resolve pending request if exists
        if original_message.id in self.pending_requests:
            self.pending_requests[original_message.id].set_result(reply_message)
            del self.pending_requests[original_message.id]

    async def publish(self, topic: str, sender: str, content: Dict):
        """
        Publish message to a topic (pub/sub).

        Args:
            topic: Topic name
            sender: Publisher agent
            content: Message content
        """
        message = Message(
            sender=sender,
            receiver="*",  # Broadcast
            type=MessageType.NOTIFICATION,
            content=content,
            topic=topic,
        )

        # Call all subscribers
        for callback in self.subscriptions.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"❌ Subscriber error in {topic}: {e}")
                self.metrics["errors"] += 1

        logger.debug(f"📢 Published to {topic}: {sender}")

    def subscribe(self, topic: str, callback: Callable):
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to
            callback: Function to call when message published
        """
        self.subscriptions[topic].append(callback)
        logger.debug(f"🔔 Subscribed to {topic}")

    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].remove(callback)

    async def _wait_for_reply(
        self, message_id: str, timeout: float
    ) -> Optional[Message]:
        """Wait for reply to a message"""
        future = asyncio.Future()
        self.pending_requests[message_id] = future

        try:
            reply = await asyncio.wait_for(future, timeout=timeout)
            return reply
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ No reply received for {message_id}")
            del self.pending_requests[message_id]
            return None

    def _add_to_history(self, message: Message):
        """Add message to history"""
        self.message_history.append(message)

        # Trim if too large
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history :]

    def get_metrics(self) -> Dict:
        """Get message bus metrics"""
        return {
            **self.metrics,
            "registered_agents": len(self.mailboxes),
            "pending_requests": len(self.pending_requests),
            "message_history_size": len(self.message_history),
            "subscriptions": {
                topic: len(callbacks) for topic, callbacks in self.subscriptions.items()
            },
        }

    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()

    async def shutdown(self):
        """Shutdown message bus"""
        logger.info("🛑 Shutting down message bus...")

        # Cancel all pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()

        self.pending_requests.clear()
        self.mailboxes.clear()
        self.subscriptions.clear()
