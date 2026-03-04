import streamlit as st


def price_data_for_item_selector():
    """ Function to get data from session_state / indexedDB for item selector """
    home_store_price_data = f'{st.session_state.db.get('item_id')}_price_data'
    price_data = st.session_state.db.get(item_id=home_store_price_data)
