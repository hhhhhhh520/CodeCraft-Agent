"""统一错误处理模块"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from functools import wraps

F = TypeVar("F", bound=Callable[..., Any])


class ErrorCode(Enum):
    """错误码枚举"""

    # LLM相关错误
    LLM_ERROR = "LLM_ERROR"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_CONNECTION_ERROR = "LLM_CONNECTION_ERROR"
    LLM_AUTH_ERROR = "LLM_AUTH_ERROR"

    # 验证相关错误
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"

    # 执行相关错误
    EXECUTION_ERROR = "EXECUTION_ERROR"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_SECURITY = "EXECUTION_SECURITY"

    # 状态相关错误
    STATE_ERROR = "STATE_ERROR"
    STATE_TRANSITION_FAILED = "STATE_TRANSITION_FAILED"

    # Agent相关错误
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_ERROR = "AGENT_ERROR"

    # 通用错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorResult:
    """统一错误结果格式

    Attributes:
        success: 是否成功
        error_code: 错误码
        error_message: 错误消息
        details: 详细信息
    """

    success: bool = False
    error_code: str = ""
    error_message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式

        Returns:
            字典格式的错误结果
        """
        return asdict(self)

    @classmethod
    def ok(cls, data: Optional[dict[str, Any]] = None) -> "ErrorResult":
        """创建成功结果

        Args:
            data: 可选的附加数据

        Returns:
            成功的ErrorResult实例
        """
        return cls(success=True, details=data or {})

    @classmethod
    def error(
        cls,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> "ErrorResult":
        """创建错误结果

        Args:
            code: 错误码
            message: 错误消息
            details: 详细信息

        Returns:
            错误的ErrorResult实例
        """
        return cls(
            success=False,
            error_code=code.value,
            error_message=message,
            details=details or {},
        )


def handle_errors(default_return: Optional[dict[str, Any]] = None) -> Callable[[F], F]:
    """错误处理装饰器

    Args:
        default_return: 发生错误时的默认返回值

    Returns:
        装饰器函数
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_result = ErrorResult.error(
                    code=ErrorCode.UNKNOWN_ERROR,
                    message=str(e),
                    details={"exception_type": type(e).__name__},
                )
                if default_return is not None:
                    return {**default_return, **error_result.to_dict()}
                return error_result.to_dict()

        return wrapper  # type: ignore

    return decorator


class CodeCraftError(Exception):
    """CodeCraft基础异常类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """初始化异常

        Args:
            code: 错误码
            message: 错误消息
            details: 详细信息
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_result(self) -> ErrorResult:
        """转换为ErrorResult

        Returns:
            ErrorResult实例
        """
        return ErrorResult.error(self.code, self.message, self.details)


class LLMError(CodeCraftError):
    """LLM相关异常"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.LLM_ERROR, message, details)


class ValidationError(CodeCraftError):
    """验证相关异常"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details)


class ExecutionError(CodeCraftError):
    """执行相关异常"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.EXECUTION_ERROR, message, details)


class StateError(CodeCraftError):
    """状态相关异常"""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.STATE_ERROR, message, details)
