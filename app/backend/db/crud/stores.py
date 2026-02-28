from common.core.super_class import SupermarketChain
from common.db.crud.stores import get_stores_for_chain
from backend.db.supabase import (get_database_url)


async def stores_for_chain(chain: SupermarketChain):
    """ This function returns item details from db"""
    DATABASE_URL = get_database_url()
    return await get_stores_for_chain(DATABASE_URL, chain=chain)

