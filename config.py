import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://tg_user:12345@localhost/tg_collector")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()