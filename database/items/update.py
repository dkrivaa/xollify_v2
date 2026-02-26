import asyncio

from common.core.super_class import SupermarketChain
from database.core.supabase import get_database_url
from common.db.crud.stores import get_stores_for_chain
from common.pipeline.fresh_price_promo import fresh_price_data


async def get_stores(chain: SupermarketChain) -> list[dict]:
    """ Get list of stores for given chain (Each store dict in list)"""
    DATABASE_URL = get_database_url()
    return await get_stores_for_chain(DATABASE_URL, chain)


async def find_store_with_most_items(stores: list[dict]):
    """ Find store with most items """
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


async def most_items_store():

    chains = await get_chains_registry()
    # List to hold results
    central_results = []

    for chain in chains[:2]:
        stores = await get_stores(chain)

        try:
            results = await find_store_with_most_items(stores)
            longest = max(results, key=lambda x: len(x['data']) if x['data'] else None)
            central_results.append({'name': chain.alias,
                                    'chain_code': longest['chain_code'],
                                    'store_code': longest['store_code'],
                                    'len': len(longest['data']) if longest else None})
        except Exception as e:
            central_results.append({'name': chain.alias,
                                    'len': None, 'error': str(e)})


        # print(longest)

    for result in central_results:
        print(result)
