"""Agent间通信协议模块"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(Enum):
    """消息类型枚举"""

    TASK_ASSIGN = "task_assign"  # 任务分配
    RESULT_RETURN = "result_return"  # 结果返回
    QUERY_REQUEST = "query_request"  # 查询请求
    FEEDBACK = "feedback"  # 反馈消息
    ERROR = "error"  # 错误消息


@dataclass
class AgentMessage:
    """Agent间通信消息

    Attributes:
        sender: 发送者名称
        receiver: 接收者名称
        msg_type: 消息类型
        payload: 消息内容
        correlation_id: 关联ID，用于追踪任务链
        timestamp: 消息时间戳
    """

    sender: str
    receiver: str
    msg_type: MessageType
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """将消息转换为字典格式

        Returns:
            包含所有消息字段的字典
        """
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "msg_type": self.msg_type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """从字典创建消息实例

        Args:
            data: 包含消息字段的字典

        Returns:
            AgentMessage实例
        """
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            msg_type=MessageType(data["msg_type"]),
            payload=data["payload"],
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", time.time()),
        )
