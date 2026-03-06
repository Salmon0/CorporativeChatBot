import asyncio
from common import setup_logger
from admin_bot import run_bot

async def main():
    await run_bot()

if __name__ == "__main__":
    setup_logger()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Программа остановлена пользователем")