import asyncio
from database import engine
from models import Base

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # раскомментируйте для полной перезаписи
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы.")

if __name__ == "__main__":
    asyncio.run(init_db())