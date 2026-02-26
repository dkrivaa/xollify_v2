import asyncio
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from common.utilities.url_to_dict import data_dict
from common.db.connection import get_session
from common.core.super_class import SupermarketChain
from database.core.models import Store
from database.core.supabase import get_database_url


# UPDATE STORES DATA IN DB ##############
async def insert_new_stores(stores_data_list: list[dict]):
    """
    Insert new stores into the database, ignoring duplicates based on chain_code and store_code.
    Params:
        stores_data_list - list of dicts of stores data for some chain
    """
    # Get the url for supabase db
    DATABASE_URL = get_database_url()
    async with await get_session(DATABASE_URL) as session:
        stmt = insert(Store).values(stores_data_list)
        stmt = stmt.on_conflict_do_nothing(index_elements=["chain_code", "store_code"])
        await session.execute(stmt)
        await session.commit()


async def update_chain_stores_db(chain):
    """ Function with flow of all steps to update a chain stores data in db"""
    # Get chain stores file from site
    url_dict = await chain.stores()
    url = url_dict.get('stores')
    cookies = url_dict.get('cookies')
    # Read and make stores url into data dict
    chain_data = await data_dict(url, cookies)
    # Prepare the data dict for insertion into db
    insert_data = await chain.extract_stores_data_for_db(chain_data)
    # Insert the data into db
    for k, v in insert_data.items():
        await insert_new_stores(v)

    return {chain.alias: 'New stores entered into db'}


async def update_stores_db():
    """
    Function to update all registered chains stores data
    Use this function to populate / update db
    """
    # Set asyncio semaphore limit (concurrent tasks)
    sem = asyncio.Semaphore(5)

    async def limited(chain):
        """ A wrapper to run function with semaphore limitation"""
        async with sem:
            return await update_chain_stores_db(chain)
    # Dict to hold results
    results = {}
    # Get list of all classes
    chains = SupermarketChain.registry

    try:
        # Make TaskGroup of tasks where each task is getting stores url (and cookies) for chain and updating db
        async with asyncio.TaskGroup() as tg:
            tasks = {}
            for chain in chains:
                tasks[chain.alias] = tg.create_task(limited(chain))

    except* Exception as eg:
        for exc in eg.exceptions:
            print("❌ Task failed:", repr(exc))
        raise  # re-raise if you want Streamlit to show error

    else:
        for name, task in tasks.items():
            results[name] = task.result()

    return results


async def get_stores_for_chain(chain: SupermarketChain):
    """ Function to get stores data for a specific chain """
    DATABASE_URL = get_database_url()
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
                # Add other fields you need
            }
            for store in stores
        ]


from common.bootstrap import initialize_backend
initialize_backend()
chain = SupermarketChain.registry[0]
stores = get_stores_for_chain(chain)
print(stores)

