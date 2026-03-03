import streamlit as st

from common.pipeline.fresh_price_promo import get_stores_price_data, get_stores_promo_data
from backend.services.async_runner import run_async


def get_stores_missing_data(stores: list[dict]) -> list[dict]:
    """
    Returns the subset of stores that are missing price or promo data.
    A store is only considered 'present' if both its price_data AND promo_data
    keys exist in session_state cache or IndexedDB.

    Args:
        stores: list of store dicts with 'chain_code' and 'store_code' keys

    Returns:
        List of stores that need fetching. Empty list means all data is present.

    Usage:
        stores_to_fetch = get_stores_missing_data(stores)
        if stores_to_fetch:
            store_data_for_selected_stores(stores_to_fetch)
    """
    cache = st.session_state.get("_idb_cache_XollifyDB_data", {})
    missing = []

    for store in stores:
        chain_code = store["chain_code"]
        store_code = store["store_code"]

        price_key = f"{chain_code}_{store_code}_price_data"
        promo_key = f"{chain_code}_{store_code}_promo_data"

        price_present = price_key in cache or st.session_state.db.exists(item_id=price_key)
        promo_present = promo_key in cache or st.session_state.db.exists(item_id=promo_key)

        if not price_present or not promo_present:
            missing.append(store)

    return missing


def store_data_for_selected_stores(stores: list[dict]):
    """ Get price and promo data for selected stores (Error: ExceptionGroup)"""
    # Check if any of the stores are missing price and promo data
    stores_to_fetch = get_stores_missing_data(stores)
    if stores_to_fetch:
        # Get data for stores
        with st.spinner('Getting Data'):
            price_data = run_async(get_stores_price_data, stores=stores_to_fetch)
            promo_data = run_async(get_stores_promo_data, stores=stores_to_fetch)

    # if data, enter into session_state and indexedDB
    if price_data:
        for data in price_data:
            item_id = f'{data['chain_code']}_{data['store_code']}_price_data'
            st.session_state.db.put(item_id=item_id, value=data)
    if promo_data:
        for data in promo_data:
            item_id = f'{data['chain_code']}_{data['store_code']}_promo_data'
            st.session_state.db.put(item_id=item_id, value=data)
