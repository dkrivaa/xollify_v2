import streamlit as st

from common.db.crud.items import get_item_from_db
from backend.services.async_runner import run_async
from ui.utilities.general import make_store_key


def data_for_store_from_db(store: dict[str, str], data_type: str = 'price'):
    """ Get price or promo data for specified store """
    # Make store key
    store_key = make_store_key(store=store, key_type=data_type)
    # Get data from db
    data = (st.session_state.db.get(item_id=store_key, default={})
            .get('value', {})
            .get('data', []))
    return data


def relevant_promos_for_item(promo_data: list[dict], item: str):

    def has_item(promo: dict, item_code: str, max_items: int = 1000) -> bool:
        items = promo.get('PromotionItems', {}).get('Item', [])

        if isinstance(items, dict):  # normalise single item to list
            items = [items]

        if len(items) > max_items:  # exclude if too many items
            return False

        return any(i.get('ItemCode') == item_code for i in items)  # check if item_code present

    return [d for d in promo_data if has_item(d, item)]


def get_item_dict_from_db(item_code: str) -> dict:
    """ Get item details from supabase db """
    DATABASE_URL = st.secrets['DATABASE_URL']
    return run_async(get_item_from_db, DATABASE_URL=DATABASE_URL, item_code=item_code)