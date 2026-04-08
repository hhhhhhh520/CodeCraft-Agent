"""任务状态机模块"""

from enum import Enum
from typing import Optional


class TaskState(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待处理
    ANALYZING = "analyzing"  # 分析中
    GENERATING = "generating"  # 生成代码中
    REVIEWING = "reviewing"  # 审查代码中
    FIXING = "fixing"  # 修复问题中
    TESTING = "testing"  # 测试中
    DONE = "done"  # 完成
    FAILED = "failed"  # 失败


class StateMachine:
    """任务状态机

    管理任务在各个状态之间的转换，确保转换符合预定义的规则。
    """

    TRANSITIONS: dict[TaskState, list[TaskState]] = {
        TaskState.PENDING: [TaskState.ANALYZING],
        TaskState.ANALYZING: [TaskState.GENERATING, TaskState.REVIEWING],
        TaskState.GENERATING: [TaskState.REVIEWING, TaskState.FAILED],
        TaskState.REVIEWING: [TaskState.TESTING, TaskState.FIXING, TaskState.DONE],
        TaskState.FIXING: [TaskState.REVIEWING, TaskState.GENERATING],
        TaskState.TESTING: [TaskState.DONE, TaskState.FIXING],
        TaskState.DONE: [],
        TaskState.FAILED: [TaskState.PENDING],
    }

    def __init__(self) -> None:
        """初始化状态机"""
        self.current_state: TaskState = TaskState.PENDING
        self.history: list[TaskState] = []

    def transition(self, next_state: TaskState) -> bool:
        """执行状态转换

        Args:
            next_state: 目标状态

        Returns:
            转换是否成功
        """
        if self.can_transition_to(next_state):
            self.history.append(self.current_state)
            self.current_state = next_state
            return True
        return False

    def can_transition_to(self, state: TaskState) -> bool:
        """检查是否可以转换到目标状态

        Args:
            state: 目标状态

        Returns:
            是否可以转换
        """
        return state in self.TRANSITIONS[self.current_state]

    def reset(self) -> None:
        """重置状态机到初始状态"""
        self.current_state = TaskState.PENDING
        self.history.clear()
