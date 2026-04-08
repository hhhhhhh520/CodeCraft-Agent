"""多Agent协调器模块"""

from typing import Any, Optional

from .context import SharedContext
from .protocol import AgentMessage, MessageType
from .state import StateMachine, TaskState


class Orchestrator:
    """多Agent协调器

    负责任务分析、分发和Agent间协调。
    """

    def __init__(self, agents: dict[str, Any], context: SharedContext) -> None:
        """初始化Orchestrator

        Args:
            agents: Agent实例字典 {name: agent}
            context: 共享上下文
        """
        self.agents = agents
        self.context = context
        self.state_machine = StateMachine()
        self.message_queue: list[AgentMessage] = []

    def process_request(self, user_request: str) -> dict:
        """处理用户请求

        Args:
            user_request: 用户请求文本

        Returns:
            处理结果
        """
        # 保存用户请求到上下文
        self.context.set("user_request", user_request)

        # 1. 任务分析
        self.state_machine.transition(TaskState.ANALYZING)
        task_type = self._analyze_task(user_request)

        # 2. 任务分发
        result = self._route_task(task_type, user_request)

        # 3. 完成处理（遵循状态转换规则）
        # GENERATING -> REVIEWING -> DONE
        if self.state_machine.current_state == TaskState.GENERATING:
            self.state_machine.transition(TaskState.REVIEWING)
        if self.state_machine.current_state == TaskState.REVIEWING:
            self.state_machine.transition(TaskState.DONE)

        return result

    def _analyze_task(self, request: str) -> str:
        """分析任务类型

        Args:
            request: 用户请求

        Returns:
            任务类型 (generate, review, debug, test)
        """
        request_lower = request.lower()

        if any(kw in request_lower for kw in ["生成", "实现", "写", "generate", "create"]):
            return "generate"
        elif any(kw in request_lower for kw in ["审查", "检查", "review", "check"]):
            return "review"
        elif any(kw in request_lower for kw in ["调试", "修复", "debug", "fix"]):
            return "debug"
        elif any(kw in request_lower for kw in ["测试", "test"]):
            return "test"
        else:
            return "generate"  # 默认生成

    def _route_task(self, task_type: str, request: str) -> dict:
        """路由任务到对应Agent

        Args:
            task_type: 任务类型
            request: 用户请求

        Returns:
            处理结果
        """
        agent_map = {
            "generate": "generator",
            "review": "reviewer",
            "debug": "debugger",
            "test": "test_generator",
        }

        agent_name = agent_map.get(task_type, "generator")

        # 如果指定的agent不存在，回退到generator
        if agent_name not in self.agents:
            agent_name = "generator"

        if agent_name in self.agents:
            self.state_machine.transition(TaskState.GENERATING)
            agent = self.agents[agent_name]
            return agent.process({"requirement": request}, self.context.data)

        return {"error": f"Agent {agent_name} not found"}

    def send_message(self, message: AgentMessage) -> Optional[dict]:
        """发送消息给指定Agent

        Args:
            message: Agent消息

        Returns:
            处理结果
        """
        if message.receiver in self.agents:
            agent = self.agents[message.receiver]
            return agent.receive_message(message)
        return None
