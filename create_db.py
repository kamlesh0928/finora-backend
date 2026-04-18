import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine
from app.models.user import User
from app.models.transaction import Transaction
from app.models.game_progress import GameProgress
from app.models.achievement import UserAchievement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Dropping existing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    logger.info("Creating all database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Database initialization completed successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
