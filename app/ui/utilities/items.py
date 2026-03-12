import streamlit as st

from common.db.crud.items import get_item_from_db
from backend.services.async_runner import run_async
from ui.utilities.general import make_store_key
from ui.elements.dialogs import alternative_dialog


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


def get_alternative_item(store: dict, item: str, ):
    """
    Get alternative item for given item.
    Used when "item_dict = next((d for d in price_data if d['ItemCode'] == item), {})" doesn't find in
    store price data
    Params:
        store - store dict where item not found
        item - item code that is missing
    """
    # Temp store key
    store_key = f"{store['chain_code']}_{store['store_code']}"
    # Price data for store from db
    price_data = data_for_store_from_db(store=store, data_type='price')

    # Check if user already selected an alternative for this store
    alt_key = f"alt_{store_key}_{item}"
    alt_item_id = st.session_state.db.get(alt_key, {})
    alt_item = alt_item_id.get('value', None)

    if alt_item:
        # Use alternative item selected in previous rerun
        effective_item = alt_item['selection']
        quantity = alt_item['quantity']
        item_dict = next((d for d in price_data if d['ItemCode'] == effective_item), {})
        return effective_item, quantity, item_dict

    # Run alternative dialog if alternative flag is raised
    flag = st.session_state.db.get(item_id='alternative_flag')
    if flag and flag.get('value', False):
        # Get item dict from supabase db
        original_dict = get_item_dict_from_db(item)
        alt_key = f"alt_{store_key}_{item}"
        # Show alternative dialog
        alternative_dialog(price_data, original_dict, store, alt_key)
        st.stop()  # Avoid continued code execution in current run
    else:
        # No alternative yet — raise flag to show alternative dialog
        st.session_state.db.put(item_id='alternative_flag', value=True)
        st.rerun()
