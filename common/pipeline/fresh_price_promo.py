import asyncio

from common.utilities.url_to_dict import data_dict
from common.core.super_class import SupermarketChain


async def fresh_price_data(chain_code: str | int, store_code: str | int, ) -> dict | None:
    """ Fetch fresh price data for the given chain and store code """
    # Get the supermarket chain class from its chain code
    chain = next((c for c in SupermarketChain.registry if c.chain_code == str(chain_code)), None)
    # Get the latest price URLs for the given chain and store code
    urls = await chain.safe_prices(store_code=store_code) if chain and store_code else None
    if urls:
        # Use pricefull URL and cookies if available
        url = urls.get('pricefull') or urls.get('PriceFull') if urls else None
        cookies = urls.get('cookies', None) if urls else None
        # Make data dict from data in pricefull URL
        price_dict = await data_dict(url=url, cookies=cookies) if url else None
        # Clean data dict to only include dicts of items
        price_data = chain.get_price_data(price_data=price_dict) if price_dict else None
        return price_data
    else:
        raise RuntimeError(f"No price URLs found for chain {chain_code} and store {store_code}.")


async def fresh_promo_data(chain_code: str | int, store_code: str | int, ) -> dict | None:
    """ Fetch fresh promo data for the given chain and store code """
    # Get the supermarket chain class from its alias
    chain = next((c for c in SupermarketChain.registry if c.chain_code == str(chain_code)), None)
    # Get the latest price URLs for the given chain and store code
    urls = await chain.safe_prices(store_code=store_code) if chain and store_code else None
    if urls:
        # Use promofull URL and cookies if available
        url = urls.get('promofull') or urls.get('PromoFull') if urls else None
        cookies = urls.get('cookies', None) if urls else None
        # Make data dict from data in pricefull URL
        promo_dict = await data_dict(url=url, cookies=cookies) if url else None
        # Clean data dict to only include dicts of items
        promo_data = chain.get_promo_data(promo_data=promo_dict) if promo_dict else None
        return promo_data
    else:
        raise RuntimeError(f"No promo URLs found for chain {chain_code} and store {store_code}.")


async def get_stores_price_data(list_of_stores: list[dict]):
    """
    Get price data for all stores in list_of_stores -
    [{'chain_code': chain_code, 'store_code': store_code}.......]
     """
    # Define size of semaphore - number of concurrent tasks
    semaphore = asyncio.Semaphore(5)

    # Define function that runs with semaphore limitation
    async def limited_fresh_price_data(chain_code, store_code):
        async with semaphore:
            result = await fresh_price_data(chain_code=chain_code, store_code=store_code)
            return {'chain_code': chain_code, 'store_code': store_code, 'data': result}

    # Get price data for all stores in list of stores
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(
                limited_fresh_price_data(
                    chain_code=store['chain_code'],
                    store_code=store['store_code']
                )
            )
            for store in list_of_stores
        ]
    # Get results of all the tasks
    results = [task.result() for task in tasks]
    return results


async def get_stores_promo_data(list_of_stores: list[dict]):
    """
    Get promo data for all stores in list_of_stores -
    [{'chain_code': chain_code, 'store_code': store_code}.......]
     """
    # Define size of semaphore - number of concurrent tasks
    semaphore = asyncio.Semaphore(5)

    # Define function that runs with semaphore limitation
    async def limited_fresh_promo_data(chain_code, store_code):
        async with semaphore:
            result = await fresh_promo_data(chain_code=chain_code, store_code=store_code)
            return {'chain_code': chain_code, 'store_code': store_code, 'data': result}

    # Get price data for all stores in list of stores
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(
                limited_fresh_promo_data(
                    chain_code=store['chain_code'],
                    store_code=store['store_code']
                )
            )
            for store in list_of_stores
        ]
    # Get results of all the tasks
    results = [task.result() for task in tasks]
    return results
