from datetime import datetime
from typing import Optional

def parse_date(date_str: str) -> Optional[datetime]:
    """Преобразует строку даты YYYY-MM-DD в объект datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def format_datetime(dt: datetime) -> str:
    """Форматирует datetime в строку 'YYYY-MM-DD HH:MM:SS'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")