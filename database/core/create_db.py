from sqlalchemy import inspect
import asyncio

from common.db.connection import get_engine, get_session
from common.db.models import Base, Store, Item
from database.core.supabase import get_database_url


# --- Function to create database ---
async def create_missing_tables(conn):
    """
    Create only tables defined in Base.metadata that do not already exist
    in the database (Supabase / Postgres).
    """

    def _sync_create(sync_conn):
        inspector = inspect(sync_conn)

        # List of table names defined in SQLAlchemy Base
        model_tables = list(Base.metadata.tables.keys())

        # Existing DB tables in the public schema
        existing_tables = inspector.get_table_names(schema="public")

        # Compute missing ones
        missing = [t for t in model_tables if t not in existing_tables]

        if not missing:
            return f"ℹ️ All tables already exist: {existing_tables}"

        # Create only missing tables
        for table_name in missing:
            table = Base.metadata.tables[table_name]
            table.create(bind=sync_conn)

        return f"✅ Created missing tables: {missing}"

    return await conn.run_sync(_sync_create)


async def create_db():
    """ Create the database and its tables if they do not already exist. """
    DATABASE_URL = get_database_url()
    engine = get_engine(DATABASE_URL)

    async with engine.begin() as conn:
        result = await create_missing_tables(conn)
        return result


