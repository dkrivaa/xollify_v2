from sqlalchemy import select

from common.core.super_class import SupermarketChain
from common.db.connection import get_session
from common.db.models import Item


async def get_item_from_db(DATABASE_URL: str, item_code: str):
    """ Function to get item data for a specific item_code """
    Session = await get_session(DATABASE_URL)

    async with Session as session:
        result = await session.execute(
            select(Item).where(Item.item_code == item_code)
        )
        item = result.scalars().first()
        if item is None:
            return None
        # Convert to serializable dicts before returning
        return {
            'ItemCode': item.item_code,
            'ItemName': item.item_name,
            'ManufacturerName': item.manufacturer_name,
            'ItemPrice': item.item_price,
            'Quantity': item.quantity,
            'UnitOfMeasure': item.unit_of_measure,
            'bIsWeighted': item.bIs_weighted,
            'ChainAlias': item.chain_alias,
            'ItemId': item.item_id,
            'ManufacturerItemDescription': item.manufacturer_item_description,
        }


async def get_items_batch_from_db(
    DATABASE_URL: str, item_codes: list[str]
) -> set[str]:
    """
    Returns the set of item_codes in the given item_codes list that exist in the DB.
    Single query regardless of list size — used for file upload validation.
    """
    if not item_codes:
        return set()

    Session = await get_session(DATABASE_URL)

    async with Session as session:
        result = await session.execute(
            select(Item.item_code).where(Item.item_code.in_(item_codes))
        )
        return {row[0] for row in result.fetchall()}

