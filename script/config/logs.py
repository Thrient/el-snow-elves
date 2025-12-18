"""日志配置模块"""
import logging
from logging.handlers import RotatingFileHandler

from script.config.Settings import settings


def setup_logging(log_level=logging.INFO, console_level=logging.DEBUG, enable_file_logging=True):
    """
    配置日志系统

    Args:
        log_level: 日志记录级别
        console_level: 控制台输出级别
        enable_file_logging: 是否启用文件日志
    """
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 清除现有的处理器（避免重复添加）
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（可选）
    if enable_file_logging:
        setup_file_logging(logger, formatter, log_level)

    return logger


def setup_file_logging(logger, formatter, log_level):
    """配置文件日志处理器"""
    # 确保日志目录存在
    settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)

    try:
        # 使用 ConcurrentRotatingFileHandler（如果可用）
        from concurrent_log_handler import ConcurrentRotatingFileHandler
        file_handler = ConcurrentRotatingFileHandler(
            str(settings.LOG_FILE),
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding=settings.LOG_ENCODING
        )
    except ImportError:
        # 回退到标准的 RotatingFileHandler
        print("未找到 cloghandler，使用标准 RotatingFileHandler")
        file_handler = RotatingFileHandler(
            str(settings.LOG_FILE),
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding=settings.LOG_ENCODING
        )

    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return file_handler


def get_logger(name: str = None):
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称，None 表示根记录器

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name) if name else logging.getLogger()
