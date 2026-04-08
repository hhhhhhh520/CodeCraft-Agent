"""Agent基类模块"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseAgent(ABC):
    """Agent基类

    定义所有Agent必须实现的接口，支持ReAct模式。
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

    def observe(self, state: dict) -> dict:
        """观察当前状态

        Args:
            state: 当前状态

        Returns:
            观察结果
        """
        return {"observation": state}

    def think(self, observation: dict) -> str:
        """推理下一步行动

        Args:
            observation: 观察结果

        Returns:
            推理结果
        """
        # 默认实现，子类可覆盖
        return f"Agent {self.name} thinking about {observation}"

    def act(self, thought: str) -> dict:
        """执行行动

        Args:
            thought: 推理结果

        Returns:
            行动结果
        """
        # 默认实现，子类可覆盖
        return {"action": "default", "thought": thought}

    def receive_message(self, message: Any) -> Optional[dict]:
        """接收消息

        Args:
            message: Agent消息

        Returns:
            处理结果
        """
        return self.process(message.payload, {})
