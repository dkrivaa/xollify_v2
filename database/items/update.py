import asyncio

from common.core.super_class import SupermarketChain
from database.core.supabase import get_database_url
from common.db.crud.stores import get_stores_for_chain
from common.pipeline.fresh_price_promo import fresh_price_data


async def get_stores(chain: SupermarketChain) -> list[dict]:
    """ Get list of stores for given chain (Each store dict in list)"""
    DATABASE_URL = get_database_url()
    return await get_stores_for_chain(DATABASE_URL, chain)


async def get_all_stores_fresh_price_data(stores: list[dict]):
    """
    Get all the fresh_price_data for all stores in given list of stores
    Params: stores
    [{
                'store_code': store.store_code,
                'store_name': store.store_name,
                'chain_code': store.chain_code,
                'chain_name': store.chain_name,
            }, .........]
    """
    semaphore = asyncio.Semaphore(5)

    async def limited_fresh_price_data(chain_code, store_code):
        async with semaphore:
            result = await fresh_price_data(chain_code=chain_code, store_code=store_code)
            return {'chain_code': chain_code, 'store_code': store_code, 'data': result}

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(
                limited_fresh_price_data(
                    chain_code=store['chain_code'],
                    store_code=store['store_code']
                )
            )
            for store in stores
        ]

    results = [task.result() for task in tasks]

    return results


async def most_items_store(chain: SupermarketChain):
    """ Function that returns list of dicts of items in store with most items for given chain """
    # Get stores for given chain
    stores = await get_stores(chain)

    try:
        results = await get_all_stores_fresh_price_data(stores)
        most_items = max(results, key=lambda x: len(x['data']) if x['data'] else None)
        return {'name': chain.alias,
                'chain_code': most_items['chain_code'],
                'store_code': most_items['store_code'],
                'data': most_items['data'] if most_items else None}
    except Exception as e:
        return {'name': chain.alias,
                'data': None, 'error': str(e)}


