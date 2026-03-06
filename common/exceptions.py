class CollectorBaseError(Exception):
    """Базовый класс для всех исключений проекта."""
    pass

class DatabaseError(CollectorBaseError):
    """Ошибка при работе с базой данных."""
    pass

class TelegramAPIError(CollectorBaseError):
    """Ошибка при взаимодействии с Telegram API."""
    pass

class PermissionDenied(CollectorBaseError):
    """Недостаточно прав для выполнения действия."""
    pass

class ConfigurationError(CollectorBaseError):
    """Ошибка в конфигурации (например, отсутствуют обязательные переменные)."""
    pass