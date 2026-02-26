from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import inspect
import asyncio

from common.db.connection import get_engine, get_session
from common.db.models import Base
from database.core.supabase import get_database_url


# --- Function to create database ---
async def tables_exist(conn) -> bool:
    """ Helper function to check if any tables exist in the database. """
    def _inspect(sync_conn):
        inspector = inspect(sync_conn)
        return bool(inspector.get_table_names())

    return await conn.run_sync(_inspect)


async def create_db():
    """ Create the database and its tables if they do not already exist. """
    DATABASE_URL = get_database_url()

    engine = get_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # Check if tables already exist
        if await tables_exist(conn):
            return "ℹ️ Tables already exist — skipping create_all()"
        # Use run_sync to call synchronous create_all in async context
        await conn.run_sync(Base.metadata.create_all)
        return "✅ Database and tables created successfully!"



