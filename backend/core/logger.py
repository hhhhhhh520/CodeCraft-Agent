"""日志系统模块"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


# 敏感信息脱敏模式
SENSITIVE_PATTERNS = [
    # API Key patterns (多种格式)
    (r"(api[_-]?key\s*[=:]\s*['\"]?)[^'\"\s,]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(\"api[_-]?key\"\s*:\s*\")[^\"]+(\")", r"\1***REDACTED***\2"),
    (r"('api[_-]?key'\s*:\s*')[^']+(')", r"\1***REDACTED***\2"),
    # Token patterns
    (r"(token\s*[=:]\s*['\"]?)[^'\"\s,]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(bearer\s+)[a-zA-Z0-9_-]+", r"\1***REDACTED***"),
    (r"(\"token\"\s*:\s*\")[^\"]+(\")", r"\1***REDACTED***\2"),
    # Password patterns
    (r"(password\s*[=:]\s*['\"]?)[^'\"\s,]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(passwd\s*[=:]\s*['\"]?)[^'\"\s,]+(['\"]?)", r"\1***REDACTED***\2"),
    # Secret patterns
    (r"(secret\s*[=:]\s*['\"]?)[^'\"\s,]+(['\"]?)", r"\1***REDACTED***\2"),
    (r"(secret_key\s*[=:]\s*['\"]?)[^'\"\s,]+(['\"]?)", r"\1***REDACTED***\2"),
    # OpenAI API Key format (sk-...)
    (r"(sk-[a-zA-Z0-9]{20,})", r"sk-***REDACTED***"),
    # DeepSeek API Key format (sk-...)
    (r"(sk-[a-f0-9]{32,})", r"sk-***REDACTED***"),
    # Anthropic API Key format
    (r"(sk-ant-[a-zA-Z0-9-]+)", r"sk-ant-***REDACTED***"),
    # JWT tokens
    (r"(eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)", r"***JWT_REDACTED***"),
    # AWS Access Key
    (r"(AKIA[A-Z0-9]{16})", r"***AWS_KEY_REDACTED***"),
    # Generic key=value patterns
    (r"(key\s*[=:]\s*['\"]?)[^'\"\s,]{8,}(['\"]?)", r"\1***REDACTED***\2"),
]


def sanitize_message(message: str) -> str:
    """脱敏敏感信息

    Args:
        message: 原始消息

    Returns:
        脱敏后的消息
    """
    sanitized = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    return sanitized


class SensitiveInfoFilter(logging.Filter):
    """敏感信息过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录中的敏感信息"""
        if record.msg:
            record.msg = sanitize_message(str(record.msg))
        if record.args:
            record.args = tuple(
                sanitize_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def setup_logger(
    name: str = "codecraft",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """设置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_file: 日志文件路径，None则不写入文件
        console: 是否输出到控制台

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 日志格式: [时间] [级别] [模块] 消息
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SensitiveInfoFilter())
        logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveInfoFilter())
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "codecraft") -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


# 默认日志配置
def init_logging(
    level: int = logging.INFO,
    log_dir: Optional[str] = None,
) -> None:
    """初始化全局日志配置

    Args:
        level: 日志级别
        log_dir: 日志目录，None则使用默认目录
    """
    if log_dir is None:
        log_dir = os.path.expanduser("~/.codecraft/logs")

    log_file = os.path.join(log_dir, f"codecraft_{datetime.now().strftime('%Y%m%d')}.log")

    setup_logger("codecraft", level=level, log_file=log_file, console=True)


# 便捷函数
def debug(msg: str) -> None:
    """记录DEBUG级别日志"""
    get_logger().debug(msg)


def info(msg: str) -> None:
    """记录INFO级别日志"""
    get_logger().info(msg)


def warning(msg: str) -> None:
    """记录WARNING级别日志"""
    get_logger().warning(msg)


def error(msg: str) -> None:
    """记录ERROR级别日志"""
    get_logger().error(msg)
