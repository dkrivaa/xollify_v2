import streamlit as st

from common.pipeline.fresh_price_promo import get_stores_price_data, get_stores_promo_data
from backend.services.async_runner import run_async
from ui.elements.dialogs import get_home_store


def check_stores_selected():
    """ Test to make sure at least one store selected """
    # Get stores / display message if no stores
    try:
        stores = st.session_state.db.get(item_id='stores')['value']
        if not stores:
            stores = []
    except TypeError as e:
        stores = []
    # If no stores:
    if not stores:
        return False
    else:
        return True


def home_store():
    """ Check if home store exist and if not display dialog """
    if st.session_state.get('home_store') or st.session_state.db.get(item_id='home_store'):
        return True
    else:
        return False


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


def remove_stale_store_data(stores: list[dict]) -> None:
    """
    Removes price and promo data from session_state and IndexedDB
    for stores that are no longer in the active stores list.
    Handles the case where session_state cache is empty (e.g. after mobile lock/resume).
    """
    # Build set of valid keys from the current stores list
    valid_keys = set()
    for store in stores:
        chain_code = store["chain_code"]
        store_code = store["store_code"]
        valid_keys.add(f"{chain_code}_{store_code}_price_data")
        valid_keys.add(f"{chain_code}_{store_code}_promo_data")

    # Get all keys from both cache and IndexedDB
    cache = st.session_state.get("_idb_cache_XollifyDB_data", {})
    cache_keys = set(cache.keys())
    idb_keys = set(st.session_state.db.get_all_keys())

    # Union — covers stale keys in either location
    all_known_keys = cache_keys | idb_keys

    # Only consider keys that are store price/promo data — ignore everything else
    store_data_keys = {
        key for key in all_known_keys
        if key.endswith("_price_data") or key.endswith("_promo_data")
    }

    stale_keys = [key for key in store_data_keys if key not in valid_keys]

    for key in stale_keys:
        st.session_state.db.delete(item_id=key)


def store_data_for_selected_stores(stores: list[dict]):
    """ Get price and promo data for selected stores (Error: ExceptionGroup)"""
    # Check if and remove stale store data in session_state / indexedDB (i.e user removed store)
    remove_stale_store_data(stores)

    # Check if any of the stores are missing price and promo data
    stores_to_fetch = get_stores_missing_data(stores)

    if stores_to_fetch:
        # Get data for stores (not already in session_state / indexedDB
        with st.spinner('Getting Data for Selected Stores'):
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
