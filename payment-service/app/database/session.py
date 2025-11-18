from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import dotenv
import os
from app.database.models import Base

dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://dev:123456789@localhost:5433/cegove")
USE_LOCAL_DB = False

# if not DATABASE_URL:
#     DATABASE_URL = "sqlite+aiosqlite:///./local.db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
