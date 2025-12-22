"""
Message system for inter-agent communication
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class MessageType(Enum):
    """Types of messages agents can exchange"""

    TASK_REQUEST = "task_request"  # Request another agent to execute a task
    TASK_RESULT = "task_result"  # Return result of a task
    QUERY = "query"  # Ask question to another agent
    QUERY_RESPONSE = "query_response"  # Answer to a query
    NOTIFICATION = "notification"  # Notify event
    VALIDATION_REQUEST = "validation_request"  # Request validation
    VALIDATION_RESULT = "validation_result"  # Validation result
    ERROR = "error"  # Error notification
    STATUS_UPDATE = "status_update"  # Status update


class MessagePriority(Enum):
    """Message priority levels"""

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Message:
    """Message exchanged between agents"""

    # Core fields
    sender: str  # Agent ID that sent the message
    receiver: str  # Agent ID that receives the message
    type: MessageType  # Type of message
    content: Dict[str, Any]  # Message payload

    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.MEDIUM

    # Threading
    reply_to: Optional[str] = None  # ID of message being replied to
    correlation_id: Optional[str] = None  # ID to correlate related messages

    # Routing
    topic: Optional[str] = None  # Pub/sub topic

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "reply_to": self.reply_to,
            "correlation_id": self.correlation_id,
            "topic": self.topic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary"""
        return cls(
            id=data["id"],
            sender=data["sender"],
            receiver=data["receiver"],
            type=MessageType(data["type"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=MessagePriority(data["priority"]),
            reply_to=data.get("reply_to"),
            correlation_id=data.get("correlation_id"),
            topic=data.get("topic"),
        )


@dataclass
class TaskRequest:
    """Request for an agent to execute a task"""

    task_type: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    priority: MessagePriority = MessagePriority.MEDIUM


@dataclass
class TaskResult:
    """Result of a task execution"""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None


@dataclass
class ValidationRequest:
    """Request to validate something"""

    target_type: str  # "code", "data", "result", etc.
    target: Any
    criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validation"""

    is_valid: bool
    confidence: float  # 0.0 to 1.0
    issues: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
