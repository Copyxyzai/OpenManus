"""
Multi-agent system for OpenManus
"""

from app.agents.base_agent import AgentConfig, BaseAgent
from app.agents.communication import (
    Message,
    MessageBus,
    MessageType,
    TaskRequest,
    TaskResult,
)

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "Message",
    "MessageType",
    "MessageBus",
    "TaskRequest",
    "TaskResult",
]
