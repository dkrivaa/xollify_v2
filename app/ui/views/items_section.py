import streamlit as st

from ui.views.general import store_data_for_selected_stores


def items_section_element():
    """ Section to show item details """
    st.write(st.session_state.db.get_all_keys())
    # Get stores
    try:
        stores = st.session_state.db.get(item_id='stores')['value']
    except TypeError as e:
        stores = []

    st.write('stores:', stores)
    # If no stores:
    if not stores:
        st.write('No Stores')
    else:
        st.write(st.session_state)
        # Get price and promo data for selected stores and store in session_state and indexedDB
        store_data_for_selected_stores(stores=stores)
        st.write('Data Saved')




