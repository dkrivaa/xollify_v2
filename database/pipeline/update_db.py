import asyncio

from common.bootstrap import initialize_backend
from common.core.super_class import SupermarketChain
from database.items.update import most_items_store, normalize_items, insert_new_items


async def update_items_database():
    """ Function to update db """
    # Initialize and register all chains
    initialize_backend()
    # Get all registered chains
    chains = SupermarketChain.registry

    for idx, chain in enumerate(chains[:2]):
        # Get data for store in chain with most items
        data = await most_items_store(chain)
        # Normalize data and insert chain and store code into dict
        normalized_data = normalize_items(data)
        # Insert items into db
        await insert_new_items(normalized_data)

        print(f'Inserted items for {chain.alias}, {idx + 1 } out of {len(chains)} chains.')




asyncio.run(update_items_database())
