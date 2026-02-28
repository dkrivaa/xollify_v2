
from common.db.crud.items import get_item_from_db
from backend.db.supabase import (get_database_url)


async def item_details(item_code: str):
    """ This function returns item details from db"""
    DATABASE_URL = get_database_url()
    return await get_item_from_db(DATABASE_URL, item_code)