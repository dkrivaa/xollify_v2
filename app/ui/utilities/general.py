import streamlit as st
import json

from common.pipeline.fresh_price_promo import get_stores_price_data, get_stores_promo_data
from backend.services.async_runner import run_async


def apply_responsive_layout():
    # CSS across app on top of each page
    st.markdown("""
    <style>
        /* Centered + max-width on desktop, full wide on mobile */
        @media (min-width: 768px) {
            .block-container {
                max-width: 860px !important;
                margin: 0 auto !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
        }

        @media (max-width: 767px) {
            .block-container {
                max-width: 100% !important;
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def make_store_key(store: dict[str, str], key_type: str = 'price') -> str:
    """ Make price or promo key for home store """
    return f'{str(store['chain_code'])}_{str(store['store_code'])}_{key_type}_data'


def sorted_stores() -> list[dict]:
    """ Sort the list of stores with home store first """
    home_store = st.session_state.db.get('home_store').get('value')
    stores = st.session_state.db.get('stores', []).get('value', [])
    return sorted(stores, key=lambda s: s['chain_code'] != home_store['chain_code']
                                        or s['store_code'] != home_store['store_code'])


def remove_home_store_from_db(stores: list[dict]):
    """ Remove home store from session_state / indexedDB if store not in stores """
    # Get the home store dict (None if not exist)
    home_store = st.session_state.db.get(item_id='home_store')
    if not home_store:
        return False
    if home_store['value'] not in stores:
        st.session_state.db.delete(item_id='home_store')
        # If deleted store is temp home store => pop
        if home_store['value'] == st.session_state.get('temp_home_store', {}):
            st.session_state.pop('temp_home_store', None)
        return True


def check_stores_selected():
    """ Test to make sure at least one store selected """
    # Get stores / display message if no stores
    stores = st.session_state.db.get(item_id='stores')
    if not stores:
        return False
    else:
        if stores['value']:
            return True


def check_home_store():
    """ Check if home store exist and if not display dialog """
    if st.session_state.db.get(item_id='home_store'):
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
    cache = st.session_state.db._cache
    missing = []

    for store in stores:
        chain_code = store["chain_code"]
        store_code = store["store_code"]

        price_key = f"{chain_code}_{store_code}_price_data"
        promo_key = f"{chain_code}_{store_code}_promo_data"

        if price_key not in cache or promo_key not in cache:
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

    # Get all keys from cache and IndexedDB
    cache = st.session_state.db._cache
    cache_keys = set(cache.keys())

    # Only consider keys that are store price/promo data — ignore everything else
    store_data_keys = {
        # key for key in all_known_keys
        key for key in cache.keys()
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
        # Guard against reruns

        cache_key = "fetch_" + "_".join(
            f"{d['chain_code']}-{d['store_code']}"
            for d in sorted(stores_to_fetch, key=lambda d: (d['chain_code'], d['store_code']))
        )

        # Evict stale fetches from session_state (previous runs for different stores if has occurred)
        for key in list(st.session_state.keys()):
            if key.startswith("fetch_") and key != cache_key:
                del st.session_state[key]

        # Run crawls only if not already fetched for this selection
        if cache_key not in st.session_state:
            with st.spinner('Getting Data for Selected Stores'):
                price_data = run_async(get_stores_price_data, stores=stores_to_fetch),
                promo_data = run_async(get_stores_promo_data, stores=stores_to_fetch),

            # TaskGroup wraps results in a tuple when run via run_until_complete
            if isinstance(price_data, tuple): price_data = list(price_data[0]) if price_data else []
            if isinstance(promo_data, tuple): promo_data = list(promo_data[0]) if promo_data else []

            import sys
            from common.indexeddb.idb import _compress
            st.write(f"price_data compressed size: {sys.getsizeof(_compress(price_data))} bytes")
            st.write(f"promo_data compressed size: {sys.getsizeof(_compress(promo_data))} bytes")
            st.write(f"price_data items: {len(price_data[0]['data'])}")
            st.write(f"promo_data items: {len(promo_data[0]['data'])}")
            st.stop()

            # Enter final data into session state and indexedDB
            if price_data:
                st.session_state.db.put_many([
                    (f"{d['chain_code']}_{d['store_code']}_price_data", d)
                    for d in price_data if d
                ])

            if promo_data:
                promo_items = [
                    (f"{d['chain_code']}_{d['store_code']}_promo_data", d)
                    for d in promo_data if d
                ]
                st.session_state.db.put_many(promo_items)

            # Mark as done — only a bool, not the data - just a placeholder
            st.session_state[cache_key] = True

