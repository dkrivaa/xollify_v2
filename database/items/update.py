import asyncio
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import cast, DateTime, func
from datetime import datetime

from common.db.connection import get_session
from common.core.super_class import SupermarketChain
from common.db.crud.stores import get_stores_for_chain
from common.pipeline.fresh_price_promo import fresh_price_data, get_stores_price_data
from common.db.models import Item
from database.core.supabase import get_database_url


# Map from raw dict keys to schema column names
KEY_MAP = {
    'PriceUpdateDate': 'price_update_date',
    'PriceUpdateTime': 'price_update_date',
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
    'UnitOfMeasurePrice': 'unit_of_measure_price',
    'AllowDiscount': 'allow_discount',
    'ItemStatus': 'item_status',
    'ItemId': 'item_id',
    'ChainAlias': 'chain_alias',
}

VALID_COLUMNS = {c.name for c in Item.__table__.columns} - {'id'}

# Dummy for min date
EPOCH = datetime(1970, 1, 1)


# GET ITEM DATA FUNCTIONS #####################
async def get_stores(chain: SupermarketChain) -> list[dict]:
    """ Get list of stores for given chain (Each store dict in list)"""
    DATABASE_URL = get_database_url()
    return await get_stores_for_chain(DATABASE_URL, chain)



async def most_items_store(chain: SupermarketChain):
    """ Function that returns list of dicts of items in store with most items for given chain """
    # Get stores for given chain
    stores = await get_stores(chain)

    try:
        results = await get_stores_price_data(stores)
        most_items = max(
            (r for r in results if r is not None and r.get('data') is not None),
            key=lambda x: len(x['data']),
            default=None
        )
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


async def insert_new_items(items_data_list: list[dict]):
    """
    Insert new items into the database, updating all fields if the new price_update_date is more recent.
    Params:
        items_data_list - list of dicts of items data
    """
    DATABASE_URL = get_database_url()

    # Deduplicate by item_code, keeping most recent price_update_date
    seen = {}
    for item in items_data_list:
        code = item['item_code']
        if code not in seen or item['price_update_date'] > seen[code]['price_update_date']:
            seen[code] = item
    items_data_list = list(seen.values())

    async with await get_session(DATABASE_URL) as session:
        batch_size = 1000
        for i in range(0, len(items_data_list), batch_size):
            batch = items_data_list[i:i + batch_size]
            stmt = insert(Item).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["item_code"],
                set_={c.name: stmt.excluded[c.name]
                      for c in Item.__table__.columns
                      if c.name != 'id'},
                where=cast(stmt.excluded.price_update_date, DateTime) >
                      func.coalesce(cast(Item.price_update_date, DateTime), EPOCH)
            )
            try:
                await session.execute(stmt)
                await session.commit()
            except Exception as e:
                print(f"Full error: {type(e).__name__}: {e}")
                raise

