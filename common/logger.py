import sys
from loguru import logger
from config import settings

def setup_logger():
    """Настраивает логгер: консольный вывод и файл с ротацией."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    logger.add(
        "logs/tg_collector.log",
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        compression="zip",
    )
    return logger

def get_logger(module_name: str):
    """Возвращает логгер с привязкой к модулю."""
    return logger.bind(module=module_name)