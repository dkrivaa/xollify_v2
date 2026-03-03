import streamlit as st

from common.pipeline.fresh_price_promo import get_stores_price_data, get_stores_promo_data
from backend.services.async_runner import run_async
from backend.services.redis import (upstash_client, upstash_save_value, upstash_append_item,
                                    upstash_get_value, upstash_delete_key)


def store_data_for_selected_stores(stores: list[dict]):
    """ Get price and promo data for selected stores """
    # Get data for stores
    with st.spinner('Getting Data'):
        price_data = run_async(get_stores_price_data, stores=stores)
        promo_data = run_async(get_stores_promo_data, stores=stores)

    # if data, enter into session_state and upstash
    if price_data:
        for data in price_data:
            item_id = f'{data['chain_code']}_{data['store_code']}_price_data'
            st.session_state.db.put(item_id=item_id, value=data)
    if promo_data:
        for data in promo_data:
            item_id = f'{data['chain_code']}_{data['store_code']}_promo_data'
            st.session_state.db.put(item_id=item_id, value=data)


def items_section_element():
    """ Section to show item details """
    # Get stores
    stores = st.session_state.db.get(item_id='stores')['value']

    # If no stores:
    if stores is None:
        st.write('No Stores')
    else:
        store_data_for_selected_stores(stores=stores)
        st.write('Data Saved')


