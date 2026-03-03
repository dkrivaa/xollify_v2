import streamlit as st

from ui.views.general import store_data_for_selected_stores


def items_section_element():
    """ Section to show item details """
    # Get stores
    try:
        stores = st.session_state.db.get(item_id='stores').get('value')
        if not stores:
            stores = []
    except TypeError as e:
        stores = []

    # If no stores:
    if not stores:
        with st.container(border=True):
            st.subheader(body=':material/error: No stores selected',
                         width='stretch',
                         text_alignment='center')
            st.markdown(body='Please Select Stores to continue',
                        width='stretch',
                        text_alignment='center')
    else:
        # Get price and promo data for selected stores and store in session_state and indexedDB
        store_data_for_selected_stores(stores=stores)
        st.write('Data Saved')




