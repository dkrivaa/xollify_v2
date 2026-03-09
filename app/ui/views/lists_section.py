import streamlit as st

from ui.utilities.workflow import enforce_workflow
from ui.utilities.lists import read_uploaded_file


def lists_section_element():
    """ Section to show shoppinglist section """
    # Checks of user selections (stores and home store) and data
    enforce_workflow()

    tab1, tab2, tab3 = st.tabs([":green[:material/upload: Upload List]",
                                ":green[:material/add_shopping_cart: Make/Add to List]",
                                ":green[:material/visibility: See List]"])

    with tab1:
        uploaded_file = st.file_uploader(label='Upload Shoppinglist',
                                         type=['csv', 'xlsx', 'xls'],
                                         key='upload_key')

        if uploaded_file:
            # Read uploaded file and return items_list - {item_code: code, quantity: int}
            items_list = read_uploaded_file(uploaded_file)
            st.write(items_list)
            st.session_state['upload_key'] = None
            # Enter items_list into session state and indexedDB
            st.session_state.db.put(item_id='items_list', value=items_list)
            st.stop()



