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

        # 3. 处理反馈闭环（如果有reviewer和debugger）
        if "reviewer" in self.agents and "debugger" in self.agents:
            result = self._handle_feedback_loop(result)
        else:
            # 没有反馈闭环时，直接完成
            # GENERATING -> REVIEWING -> DONE (遵循状态转换规则)
            if self.state_machine.current_state == TaskState.GENERATING:
                self.state_machine.transition(TaskState.REVIEWING)
            if self.state_machine.current_state == TaskState.REVIEWING:
                self.state_machine.transition(TaskState.DONE)

        # 4. 标记完成（如果尚未完成）
        if self.state_machine.current_state != TaskState.DONE:
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

    def _handle_feedback_loop(self, result: dict, max_iterations: int = 3) -> dict:
        """处理反馈闭环

        Args:
            result: 初始结果
            max_iterations: 最大迭代次数

        Returns:
            最终结果
        """
        iteration = 0

        while iteration < max_iterations:
            # 审查阶段
            if self.state_machine.current_state == TaskState.GENERATING:
                self.state_machine.transition(TaskState.REVIEWING)

            if self.state_machine.current_state == TaskState.REVIEWING:
                review_result = self.agents["reviewer"].process(
                    {"code": result.get("code", "")},
                    self.context.data,
                )

                if review_result.get("passed", True):
                    # 审查通过，完成
                    self.state_machine.transition(TaskState.DONE)
                    return result
                else:
                    # 审查不通过，进入修复
                    self.state_machine.transition(TaskState.FIXING)
                    result["issues"] = review_result.get("issues", [])
                    result["review_score"] = review_result.get("score", 0)

            # 修复阶段
            if self.state_machine.current_state == TaskState.FIXING:
                fix_result = self.agents["debugger"].process(
                    {
                        "code": result.get("code", ""),
                        "issues": result.get("issues", []),
                    },
                    self.context.data,
                )
                result["code"] = fix_result.get("fixed_code", result.get("code", ""))
                self.state_machine.transition(TaskState.REVIEWING)
                iteration += 1

        # 达到最大迭代次数
        return result
