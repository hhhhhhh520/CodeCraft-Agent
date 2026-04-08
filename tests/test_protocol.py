# tests/test_protocol.py
"""通信协议单元测试"""

import pytest
from backend.core.protocol import MessageType, AgentMessage


class TestMessageType:
    """MessageType枚举测试"""

    def test_message_type_values(self):
        """测试消息类型值"""
        assert MessageType.TASK_ASSIGN.value == "task_assign"
        assert MessageType.RESULT_RETURN.value == "result_return"
        assert MessageType.QUERY_REQUEST.value == "query_request"
        assert MessageType.FEEDBACK.value == "feedback"
        assert MessageType.ERROR.value == "error"


class TestAgentMessage:
    """AgentMessage测试"""

    def test_create_message(self):
        """测试创建消息"""
        msg = AgentMessage(
            sender="orchestrator",
            receiver="generator",
            msg_type=MessageType.TASK_ASSIGN,
            payload={"task": "generate code"},
        )
        assert msg.sender == "orchestrator"
        assert msg.receiver == "generator"
        assert msg.msg_type == MessageType.TASK_ASSIGN
        assert msg.payload == {"task": "generate code"}
        assert msg.correlation_id is not None
        assert msg.timestamp > 0

    def test_message_to_dict(self):
        """测试消息序列化"""
        msg = AgentMessage(
            sender="reviewer",
            receiver="debugger",
            msg_type=MessageType.FEEDBACK,
            payload={"issues": ["bug on line 10"]},
        )
        result = msg.to_dict()
        assert result["sender"] == "reviewer"
        assert result["receiver"] == "debugger"
        assert result["msg_type"] == "feedback"
        assert result["payload"] == {"issues": ["bug on line 10"]}
        assert "correlation_id" in result
        assert "timestamp" in result

    def test_message_unique_correlation_id(self):
        """测试每条消息有唯一的correlation_id"""
        msg1 = AgentMessage(
            sender="a", receiver="b", msg_type=MessageType.TASK_ASSIGN, payload={}
        )
        msg2 = AgentMessage(
            sender="a", receiver="b", msg_type=MessageType.TASK_ASSIGN, payload={}
        )
        assert msg1.correlation_id != msg2.correlation_id

    def test_message_timestamp_order(self):
        """测试消息时间戳顺序"""
        import time

        msg1 = AgentMessage(
            sender="a", receiver="b", msg_type=MessageType.TASK_ASSIGN, payload={}
        )
        time.sleep(0.01)
        msg2 = AgentMessage(
            sender="a", receiver="b", msg_type=MessageType.TASK_ASSIGN, payload={}
        )
        assert msg2.timestamp > msg1.timestamp
