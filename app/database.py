import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Load environment variables
load_dotenv()

db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/dbname")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

if "?sslmode=" in db_url:
    db_url = db_url.replace("?sslmode=", "?ssl=")
elif "&sslmode=" in db_url:
    db_url = db_url.replace("&sslmode=", "&ssl=")

db_url = db_url.replace("&channel_binding=require", "")
db_url = db_url.replace("?channel_binding=require", "")

engine = create_async_engine(
    db_url,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables. Call once at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose the engine pool on shutdown."""
    await engine.dispose()
