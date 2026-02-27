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

        # Convert to serializable dicts before returning
        return [
            {
                'item_code': item.item_code,
                'item_name': item.item_name,

            }

        ]