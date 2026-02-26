from sqlalchemy import select

from common.core.super_class import SupermarketChain
from common.db.connection import get_session
from common.db.models import Store


async def get_stores_for_chain(DATABASE_URL: str, chain: SupermarketChain):
    """ Function to get stores data for a specific chain """
    Session = await get_session(DATABASE_URL)

    async with Session as session:
        result = await session.execute(
            select(Store).where(Store.chain_code == chain.chain_code)
        )
        stores = result.scalars().all()

        # Convert to serializable dicts before returning
        return [
            {
                'store_code': store.store_code,
                'store_name': store.store_name,
                'chain_code': store.chain_code,
                'chain_name': store.chain_name,
            }
            for store in stores
        ]