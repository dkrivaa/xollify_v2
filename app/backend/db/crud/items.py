async def test_item(item_code: str):
    from common.db.crud.items import get_item_from_db
    DATABASE_URL = get_database_url()

    return await get_item_from_db(DATABASE_URL, item_code)