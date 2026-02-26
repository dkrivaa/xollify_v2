import asyncio

from common.core.super_class import SupermarketChain
from database.core.supabase import get_database_url
from common.db.crud.stores import get_stores_for_chain
from common.pipeline.fresh_price_promo import fresh_price_data
from common.db.models import Item


# Map from raw dict keys to schema column names
KEY_MAP = {
    'PriceUpdateDate': 'price_update_date',
    'ItemCode': 'item_code',
    'ItemType': 'item_type',
    'ItemName': 'item_name',
    'ItemNm': 'item_name',  # alternate key
    'ManufacturerName': 'manufacturer_name',
    'ManufactureCountry': 'manufacture_country',
    'ManufacturerItemDescription': 'manufacturer_item_description',
    'UnitQty': 'unit_qty',
    'Quantity': 'quantity',
    'bIsWeighted': 'bIs_weighted',
    'UnitOfMeasure': 'unit_of_measure',
    'QtyInPackage': 'qty_in_package',
    'ItemPrice': 'item_price',
    'UnitOfMeasurePrice': 'unit_of_measure_rice',
    'AllowDiscount': 'allow_discount',
    'ItemStatus': 'item_status',
    'ItemId': 'item_id',
    'ChainAlias': 'chain_alias',
}

VALID_COLUMNS = {c.name for c in Item.__table__.columns} - {'id'}


# GET ITEM DATA FUNCTIONS #####################
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


# GET ITEM DATA READY INSERT INTO DB
def normalize_item(d: dict, chain_code: str, store_code: str) -> dict:
    """ Adjust keys to column names in db table """
    # Rename keys in item dict
    renamed = {KEY_MAP.get(k, k): v for k, v in d.items()}
    # Filter out keys not in db table
    filtered = {k: v for k, v in renamed.items() if k in VALID_COLUMNS}
    # Add chain_code and store_code
    filtered['chain_code'] = chain_code
    filtered['store_code'] = store_code
    return filtered


def normalize_items(most_items_store: dict) -> list[dict]:
    """
    Function that takes most_items_store as input and returns list of items dicts
    ready for insert into db table
    """
    chain_code = most_items_store['chain_code']
    store_code = most_items_store['store_code']
    items = most_items_store['data']
    return [normalize_item(item, chain_code, store_code) for item in items]


