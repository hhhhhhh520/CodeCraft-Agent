"""多Agent协调器模块"""

import logging
from typing import Any, Optional

from .context import SharedContext
from .errors import ErrorCode, ErrorResult
from .protocol import AgentMessage, MessageType
from .state import StateMachine, TaskState

logger = logging.getLogger("codecraft.orchestrator")


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
        logger.info(f"Processing request: {user_request[:50]}...")

        # 保存用户请求到上下文
        self.context.set("user_request", user_request)

        # 1. 任务分析
        if not self.state_machine.transition(TaskState.ANALYZING):
            logger.error("Failed to transition to ANALYZING state")
            return ErrorResult.error(
                ErrorCode.STATE_TRANSITION_FAILED,
                f"Cannot transition from {self.state_machine.current_state} to ANALYZING",
            ).to_dict()

        task_type = self._analyze_task(user_request)
        logger.debug(f"Task type identified: {task_type}")

        # 2. 任务分发
        result = self._route_task(task_type, user_request)

        # 检查路由结果
        if "error" in result and "code" not in result:
            logger.error(f"Task routing failed: {result.get('error')}")
            return result

        # 3. 处理反馈闭环（如果有reviewer和debugger）
        if "reviewer" in self.agents and "debugger" in self.agents:
            result = self._handle_feedback_loop(result)
        else:
            # 没有反馈闭环时，直接完成
            # GENERATING -> REVIEWING -> DONE (遵循状态转换规则)
            if self.state_machine.current_state == TaskState.GENERATING:
                if not self.state_machine.transition(TaskState.REVIEWING):
                    logger.warning("Failed to transition to REVIEWING state")
            if self.state_machine.current_state == TaskState.REVIEWING:
                if not self.state_machine.transition(TaskState.DONE):
                    logger.warning("Failed to transition to DONE state")

        # 4. 标记完成（如果尚未完成）
        if self.state_machine.current_state != TaskState.DONE:
            if not self.state_machine.transition(TaskState.DONE):
                logger.warning("Failed to transition to DONE state")

        logger.info("Request processing completed")
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
            if not self.state_machine.transition(TaskState.GENERATING):
                logger.error(f"Failed to transition to GENERATING state")
                return ErrorResult.error(
                    ErrorCode.STATE_TRANSITION_FAILED,
                    f"Cannot transition to GENERATING",
                ).to_dict()

            agent = self.agents[agent_name]
            try:
                logger.debug(f"Routing task to agent: {agent_name}")
                result = agent.process({"requirement": request}, self.context.data)

                # 检查返回值有效性
                if result is None:
                    logger.error(f"Agent {agent_name} returned None")
                    return ErrorResult.error(
                        ErrorCode.AGENT_ERROR,
                        f"Agent {agent_name} returned None",
                    ).to_dict()

                if not isinstance(result, dict):
                    logger.error(f"Agent {agent_name} returned invalid type: {type(result)}")
                    return ErrorResult.error(
                        ErrorCode.AGENT_ERROR,
                        f"Agent {agent_name} returned invalid type: {type(result)}",
                    ).to_dict()

                return result

            except Exception as e:
                logger.exception(f"Agent {agent_name} raised exception")
                return ErrorResult.error(
                    ErrorCode.AGENT_ERROR,
                    f"Agent {agent_name} failed: {str(e)}",
                    {"exception_type": type(e).__name__},
                ).to_dict()

        return ErrorResult.error(
            ErrorCode.AGENT_NOT_FOUND,
            f"Agent {agent_name} not found",
        ).to_dict()

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
                if not self.state_machine.transition(TaskState.REVIEWING):
                    logger.warning("Failed to transition to REVIEWING in feedback loop")
                    break

            if self.state_machine.current_state == TaskState.REVIEWING:
                try:
                    review_result = self.agents["reviewer"].process(
                        {"code": result.get("code", "")},
                        self.context.data,
                    )

                    if review_result is None or not isinstance(review_result, dict):
                        logger.error("Reviewer returned invalid result")
                        break

                except Exception as e:
                    logger.exception("Reviewer raised exception")
                    break

                if review_result.get("passed", True):
                    # 审查通过，进入测试阶段
                    result["review_score"] = review_result.get("score", 100)

                    # 如果有 test_generator，执行测试生成
                    if "test_generator" in self.agents:
                        if not self.state_machine.transition(TaskState.TESTING):
                            logger.warning("Failed to transition to TESTING")
                            break

                        try:
                            test_result = self.agents["test_generator"].process(
                                {"code": result.get("code", "")},
                                self.context.data,
                            )
                            if test_result and isinstance(test_result, dict):
                                result["test_code"] = test_result.get("test_code", "")
                                result["test_passed"] = test_result.get("passed", True)
                        except Exception as e:
                            logger.warning(f"Test generation failed: {e}")

                    # 测试完成，标记完成
                    if not self.state_machine.transition(TaskState.DONE):
                        logger.warning("Failed to transition to DONE after review pass")
                    return result
                else:
                    # 审查不通过，进入修复
                    if not self.state_machine.transition(TaskState.FIXING):
                        logger.warning("Failed to transition to FIXING")
                        break
                    result["issues"] = review_result.get("issues", [])
                    result["review_score"] = review_result.get("score", 0)

            # 修复阶段
            if self.state_machine.current_state == TaskState.FIXING:
                try:
                    fix_result = self.agents["debugger"].process(
                        {
                            "code": result.get("code", ""),
                            "issues": result.get("issues", []),
                        },
                        self.context.data,
                    )

                    if fix_result is None or not isinstance(fix_result, dict):
                        logger.error("Debugger returned invalid result")
                        break

                except Exception as e:
                    logger.exception("Debugger raised exception")
                    break

                result["code"] = fix_result.get("fixed_code", result.get("code", ""))

                if not self.state_machine.transition(TaskState.REVIEWING):
                    logger.warning("Failed to transition back to REVIEWING")
                    break

                iteration += 1

        # 达到最大迭代次数
        logger.info(f"Feedback loop completed after {iteration} iterations")
        return result
