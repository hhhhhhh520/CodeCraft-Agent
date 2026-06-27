"""Agent基类模块"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseAgent(ABC):
    """Agent基类

    定义所有Agent必须实现的接口。
    """

    def __init__(
        self,
        name: str,
        llm: Any,
        tools: list[Any],
        memory: Optional[Any] = None,
    ) -> None:
        """初始化Agent

        Args:
            name: Agent名称
            llm: LLM实例
            tools: 工具列表
            memory: 记忆系统实例（可选）
        """
        self.name = name
        self.llm = llm
        self.tools = tools
        self.memory = memory

    @abstractmethod
    def process(self, input_data: dict, context: dict) -> dict:
        """处理任务

        Args:
            input_data: 输入数据
            context: 共享上下文

        Returns:
            处理结果
        """
        pass

    def receive_message(self, message: Any) -> Optional[dict]:
        """接收消息

        Args:
            message: Agent消息

        Returns:
            处理结果
        """
        return self.process(message.payload, {})
