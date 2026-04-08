# tests/test_state.py
"""状态机单元测试"""

import pytest
from backend.core.state import TaskState, StateMachine


class TestTaskState:
    """TaskState枚举测试"""

    def test_state_values(self):
        """测试状态值"""
        assert TaskState.PENDING.value == "pending"
        assert TaskState.ANALYZING.value == "analyzing"
        assert TaskState.GENERATING.value == "generating"
        assert TaskState.REVIEWING.value == "reviewing"
        assert TaskState.FIXING.value == "fixing"
        assert TaskState.TESTING.value == "testing"
        assert TaskState.DONE.value == "done"
        assert TaskState.FAILED.value == "failed"


class TestStateMachine:
    """StateMachine测试"""

    def test_initial_state(self):
        """测试初始状态为PENDING"""
        sm = StateMachine()
        assert sm.current_state == TaskState.PENDING

    def test_valid_transition(self):
        """测试有效状态转换"""
        sm = StateMachine()
        assert sm.transition(TaskState.ANALYZING) is True
        assert sm.current_state == TaskState.ANALYZING

    def test_invalid_transition(self):
        """测试无效状态转换"""
        sm = StateMachine()
        assert sm.transition(TaskState.DONE) is False
        assert sm.current_state == TaskState.PENDING

    def test_transition_history(self):
        """测试转换历史记录"""
        sm = StateMachine()
        sm.transition(TaskState.ANALYZING)
        sm.transition(TaskState.GENERATING)
        assert len(sm.history) == 2
        assert sm.history[0] == TaskState.PENDING
        assert sm.history[1] == TaskState.ANALYZING

    def test_can_transition_to(self):
        """测试状态转换检查"""
        sm = StateMachine()
        assert sm.can_transition_to(TaskState.ANALYZING) is True
        assert sm.can_transition_to(TaskState.DONE) is False

    def test_full_workflow(self):
        """测试完整工作流"""
        sm = StateMachine()
        # PENDING -> ANALYZING
        assert sm.transition(TaskState.ANALYZING) is True
        # ANALYZING -> GENERATING
        assert sm.transition(TaskState.GENERATING) is True
        # GENERATING -> REVIEWING
        assert sm.transition(TaskState.REVIEWING) is True
        # REVIEWING -> TESTING
        assert sm.transition(TaskState.TESTING) is True
        # TESTING -> DONE
        assert sm.transition(TaskState.DONE) is True
        assert sm.current_state == TaskState.DONE

    def test_fixing_loop(self):
        """测试修复循环"""
        sm = StateMachine()
        sm.transition(TaskState.ANALYZING)
        sm.transition(TaskState.GENERATING)
        sm.transition(TaskState.REVIEWING)
        # REVIEWING -> FIXING
        assert sm.transition(TaskState.FIXING) is True
        # FIXING -> REVIEWING
        assert sm.transition(TaskState.REVIEWING) is True

    def test_failed_state(self):
        """测试失败状态"""
        sm = StateMachine()
        sm.transition(TaskState.ANALYZING)
        sm.transition(TaskState.GENERATING)
        # GENERATING -> FAILED
        assert sm.transition(TaskState.FAILED) is True
        # FAILED -> PENDING (重试)
        assert sm.transition(TaskState.PENDING) is True
