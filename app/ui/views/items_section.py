import streamlit as st

from common.pipeline.fresh_price_promo import get_stores_price_data, get_stores_promo_data
from backend.services.indexeddb_session import SessionIndexedDB
from backend.services.async_runner import run_async
from backend.services.redis import (upstash_client, upstash_save_value, upstash_append_item,
                                    upstash_get_value, upstash_delete_key)


def store_data_for_selected_stores(stores: list[dict]):
    """ Get price and promo data for selected stores """
    # Get data for stores
    with st.spinner('Getting Data'):
        price_data = run_async(get_stores_price_data, stores=stores)
        promo_data = run_async(get_stores_promo_data, stores=stores)

    st.write(price_data)
    st.write(promo_data)
    # if data, enter into session_state and upstash
    # redis_client = upstash_client()
    if price_data:
        for data in price_data:
            item_id = f'{data['chain_code']}_{data['store_code']}_price_data'
            SessionIndexedDB.put(item_id=item_id, value=data)
            # upstash_save_value(redis_client, f'{data['chain_code']}_{data['store_code']}_price_data', data)
    if promo_data:
        for data in promo_data:
            upstash_save_value(redis_client, f'{data['chain_code']}_{data['store_code']}_promo_data', data)


def items_section_element():
    """ Section to show item details """
    # Get stores
    redis_client = upstash_client()
    stores = upstash_get_value(redis_client, 'stores')

    # If no stores:
    if stores is None:
        st.write('No Stores')
    else:
        store_data_for_selected_stores(stores=stores)
        st.write('Data Saved')


