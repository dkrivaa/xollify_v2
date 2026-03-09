import streamlit as st

from ui.utilities.workflow import enforce_workflow
from ui.utilities.lists import read_uploaded_file


def lists_section_element():
    """ Section to show shoppinglist section """
    # Checks of user selections (stores and home store) and data
    enforce_workflow()

    # init message flag
    if 'show_upload_message' not in st.session_state:
        st.session_state['show_upload_message'] = False

    tab1, tab2 = st.tabs([":green[:material/upload: Upload Shopping List]",
                          ":green[:material/visibility: Make/Edit Shopping List]",])

    with tab1:
        # Counter to clear file_upload after file read
        if 'uploader_counter' not in st.session_state:
            st.session_state.uploader_counter = 0
        # Upload widget
        uploaded_file = st.file_uploader(label='Upload Shoppinglist',
                                         type=['csv', 'xlsx', 'xls'],
                                         key=f'uploader_{st.session_state.uploader_counter}')

        if uploaded_file:
            st.session_state['show_upload_message'] = True
            # Read uploaded file and return items_list - {item_code: code, quantity: int}
            items_list = read_uploaded_file(uploaded_file)
            # Add to uploader_counter - clear upload widget when rerun
            st.session_state.uploader_counter += 1
            # Enter items_list into session state and indexedDB
            st.session_state.db.put(item_id='items_list', value=items_list)

        # Message
        if (st.session_state['show_upload_message']
                and st.session_state.db.get(item_id='items_list', default={})):
            st.success('Shopping list uploaded successfully. To add or edit the list - '
                       'goto "Make/Edit Shopping List"')
            st.session_state['show_upload_message'] = False



