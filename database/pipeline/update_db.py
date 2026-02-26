import asyncio

from common.bootstrap import initialize_backend
from common.core.super_class import SupermarketChain
from database.items.update import most_items_store

async def update_database():
    """ Function to update db """
    # Initialize and register all chains
    initialize_backend()
    # Get all registered chains
    chains = SupermarketChain.registry


    chain = chains[0]
    data = await most_items_store(chain)

    for key in list(data.keys())[:3]:
        print(data[key])


asyncio.run(update_database())
