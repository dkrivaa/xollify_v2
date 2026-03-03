import streamlit as st

from ui.views.general import check_stores_selected, home_store, store_data_for_selected_stores
from ui.elements.dialogs import get_home_store
from ui.elements.static import no_stores_selected



def items_section_element():
    """ Section to show item details """
    # LOGICAL TESTS ############
    # Check store/s selected
    stores_exist = check_stores_selected()
    if not stores_exist:
        no_stores_selected()
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







