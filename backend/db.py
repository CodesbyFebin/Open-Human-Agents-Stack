"""Async SQLAlchemy engine + session management."""
from __future__ import annotations

import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://openminds:openminds@localhost:5432/openminds")

engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=20, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

async def init_db():
    """Create tables if they don't exist (for non-Docker dev)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
