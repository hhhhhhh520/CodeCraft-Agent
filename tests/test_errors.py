"""错误处理模块测试"""

import pytest
from backend.core.errors import ErrorCode, ErrorResult, handle_errors


class TestErrorCode:
    """ErrorCode枚举测试"""

    def test_error_code_values(self):
        """测试错误码值"""
        assert ErrorCode.LLM_ERROR.value == "LLM_ERROR"
        assert ErrorCode.LLM_RATE_LIMIT.value == "LLM_RATE_LIMIT"
        assert ErrorCode.STATE_TRANSITION_FAILED.value == "STATE_TRANSITION_FAILED"
        assert ErrorCode.AGENT_NOT_FOUND.value == "AGENT_NOT_FOUND"

    def test_error_code_categories(self):
        """测试错误码分类完整性"""
        # LLM相关
        assert hasattr(ErrorCode, "LLM_ERROR")
        assert hasattr(ErrorCode, "LLM_RATE_LIMIT")
        assert hasattr(ErrorCode, "LLM_CONNECTION_ERROR")
        assert hasattr(ErrorCode, "LLM_AUTH_ERROR")

        # 验证相关
        assert hasattr(ErrorCode, "VALIDATION_ERROR")
        assert hasattr(ErrorCode, "INVALID_INPUT")
        assert hasattr(ErrorCode, "MISSING_FIELD")

        # 执行相关
        assert hasattr(ErrorCode, "EXECUTION_ERROR")
        assert hasattr(ErrorCode, "EXECUTION_TIMEOUT")
        assert hasattr(ErrorCode, "EXECUTION_SECURITY")

        # 状态相关
        assert hasattr(ErrorCode, "STATE_ERROR")
        assert hasattr(ErrorCode, "STATE_TRANSITION_FAILED")

        # Agent相关
        assert hasattr(ErrorCode, "AGENT_NOT_FOUND")
        assert hasattr(ErrorCode, "AGENT_ERROR")


class TestErrorResult:
    """ErrorResult测试"""

    def test_ok_result(self):
        """测试成功结果"""
        result = ErrorResult.ok()
        assert result.success is True
        assert result.error_code == ""
        assert result.error_message == ""
        assert result.details == {}

    def test_ok_result_with_data(self):
        """测试带数据的成功结果"""
        data = {"code": "def hello(): pass"}
        result = ErrorResult.ok(data)
        assert result.success is True
        assert result.details == data

    def test_error_result(self):
        """测试错误结果"""
        result = ErrorResult.error(
            ErrorCode.LLM_ERROR,
            "API调用失败",
            {"status_code": 500}
        )
        assert result.success is False
        assert result.error_code == "LLM_ERROR"
        assert result.error_message == "API调用失败"
        assert result.details == {"status_code": 500}

    def test_error_result_without_details(self):
        """测试无详情的错误结果"""
        result = ErrorResult.error(ErrorCode.UNKNOWN_ERROR, "未知错误")
        assert result.success is False
        assert result.error_code == "UNKNOWN_ERROR"
        assert result.details == {}

    def test_to_dict(self):
        """测试转换为字典"""
        result = ErrorResult.error(ErrorCode.VALIDATION_ERROR, "输入无效")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["success"] is False
        assert d["error_code"] == "VALIDATION_ERROR"
        assert d["error_message"] == "输入无效"


class TestHandleErrors:
    """handle_errors装饰器测试"""

    def test_normal_function(self):
        """测试正常函数执行"""
        @handle_errors()
        def add(a: int, b: int) -> int:
            return a + b

        result = add(1, 2)
        assert result == 3

    def test_exception_returns_error_dict(self):
        """测试异常返回错误字典"""
        @handle_errors()
        def fail():
            raise ValueError("测试错误")

        result = fail()
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["error_code"] == "UNKNOWN_ERROR"
        assert "测试错误" in result["error_message"]
        assert result["details"]["exception_type"] == "ValueError"

    def test_exception_with_default_return(self):
        """测试异常返回带默认值的错误字典"""
        @handle_errors(default_return={"status": "error"})
        def fail():
            raise RuntimeError("运行时错误")

        result = fail()
        assert result["status"] == "error"
        assert result["success"] is False

    def test_preserves_return_type(self):
        """测试正常返回值不受影响"""
        @handle_errors()
        def get_string() -> str:
            return "hello"

        result = get_string()
        assert result == "hello"
