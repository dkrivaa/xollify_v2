import streamlit as st

from ui.elements.static import logo
from common.core.super_class import SupermarketChain
from ui.utilities.workflow import WorkflowStep, enforce_workflow
from ui.utilities.lists import read_uploaded_file, shoppinglist_for_store
from ui.utilities.items import (data_for_store_from_db, relevant_promos_for_item,
                                get_item_dict_from_db, get_alternative_item)
from ui.utilities.general import sorted_stores
from ui.elements.dynamic import item_selector, price_element, promo_element


def render():
    """ The main function to display shoppinglist page """
    logo()
    st.divider()
    st.space()

    # Check all in workflow, incl. getting data for stores
    enforce_workflow()

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body=':blue[All ready!!]')

        # Counter to clear file_upload after file read
        if 'uploader_counter' not in st.session_state:
            st.session_state.uploader_counter = 0
        # Upload widget
        uploaded_file = st.file_uploader(label='Upload Shoppinglist',
                                         type=['csv', 'xlsx', 'xls'],
                                         key=f'uploader_{st.session_state.uploader_counter}')

        if uploaded_file:
            # # Set flag to clear file uploader widget
            # st.session_state['show_upload_message'] = True
            # Read uploaded file and return items_list - {item_code: code, quantity: int}
            items_list = read_uploaded_file(uploaded_file)
            # Add to uploader_counter => clear upload widget when rerun
            st.session_state.uploader_counter += 1
            # Enter items_list into session state and indexedDB
            st.session_state.db.put(item_id='items_list', value=items_list)

        stores = st.session_state.db.get('stores').get('value', {})
        # Order stores list so home store is first
        stores = sorted(stores, key=lambda d: d != st.session_state.db.get('home_store').get('value'))
        for store in stores:
            # Check if store has already been handled and has shoppinglist (flag for js_eval reruns)
            item_id = f"{store['chain_code']}_{store['store_code']}_shoppinglist"
            if st.session_state.db.get(item_id=item_id):
                continue
            else:
                # Make shopping list for store
                shoppinglist = shoppinglist_for_store(store=store)
                st.write(shoppinglist)
                if shoppinglist:
                    st.session_state.db.put(item_id=item_id, value=shoppinglist)



if __name__ == "__main__":
    render()