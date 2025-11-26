from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import dotenv
import os
from app.database.models import Base

dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ⇩ If empty → fallback to SQLite
if not DATABASE_URL or DATABASE_URL.strip() == "":
    DATABASE_URL = "sqlite+aiosqlite:///./payment_service.db"
    USE_LOCAL_DB = True
else:
    USE_LOCAL_DB = False

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

AsyncSessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db():
    """Create tables if using local SQLite."""
    async with engine.begin() as conn:
        # Only auto-create schema for SQLite fallback
        if USE_LOCAL_DB:
            await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
