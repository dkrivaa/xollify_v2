from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine, async_sessionmaker, )
import os
from dotenv import load_dotenv


def get_engine(database_url: str):
    """ Create and return an asynchronous SQLAlchemy engine. """
    engine = create_async_engine(database_url, echo=True, pool_pre_ping=True,
                                 connect_args={"statement_cache_size": 0, },  # 🔑 REQUIRED for Supabase
                                 )
    return engine


async def get_session(database_url: str) -> AsyncSession:
    """ Create and return an asynchronous SQLAlchemy session. """
    engine = get_engine(database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return async_session()


