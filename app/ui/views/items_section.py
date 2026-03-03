import streamlit as st

from ui.views.general import store_data_for_selected_stores, home_store
from ui.elements.dialogs import get_home_store



def check_stores_selected():
    """ Test to make sure at least one store selected """
    # Get stores / display message if no stores
    try:
        stores = st.session_state.db.get(item_id='stores').get('value')
        if not stores:
            stores = []
    except TypeError as e:
        stores = []
    # If no stores:
    if not stores:
        return False
    else:
        return True


def items_section_element():
    """ Section to show item details """
    # LOGICAL TESTS ############
    # Check store/s selected
    stores_exist = check_stores_selected()
    if not stores_exist:
        with st.container(border=True):
            st.subheader(body=':material/error: No stores selected',
                         width='stretch',
                         text_alignment='center')
            st.markdown(body='Please Select Stores to continue',
                        width='stretch',
                        text_alignment='center')
    # check home store selected
    home_store_selected = home_store()
    if not home_store_selected:
        get_home_store()
    # END OF LOGICAL TESTS ################

    # Get price and promo data for selected stores and enter into session_state and indexedDB
    # Automatically checks if store data already entered and removes stale store data
    stores = st.session_state.db.get(item_id='stores').get('value')
    store_data_for_selected_stores(stores=stores)
    st.write('Data Saved')







