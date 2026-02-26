from common.core.super_class import SupermarketChain
from common.db.crud.stores import get_stores_for_chain
from database.core.supabase import get_database_url





async def get_stores(chain: SupermarketChain):
    """ Function to get stores data for a specific chain """
    DATABASE_URL = get_database_url()
    stores = get_stores_for_chain(DATABASE_URL=DATABASE_URL, chain=chain)
    return stores

