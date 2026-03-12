import streamlit as st

from ui.utilities.workflow import WorkflowStep, enforce_workflow
from ui.utilities.lists import read_uploaded_file, enrich_items_list
from ui.utilities.general import make_store_key
from ui.utilities.items import data_for_store_from_db


def lists_section_element():
    """ Section to show shoppinglist section """
    # Checks of user selections (stores and home store) and data
    # check stores exist
    enforce_workflow(required=WorkflowStep.NO_STORES)

    # Set temp home store
    stores = st.session_state.db.get(item_id='stores').get('value', [])
    if len(stores) == 1:
        st.session_state['temp_home_store'] = stores[0]

    # Check all in workflow, incl. getting data for stores
    enforce_workflow()

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
            # Add to uploader_counter => clear upload widget when rerun
            st.session_state.uploader_counter += 1
            # Enter items_list into session state and indexedDB
            st.session_state.db.put(item_id='items_list', value=items_list)


    with tab2:
        # Display and make / add / edit items_list

        # Get price data for "Home Store"
        home_store = st.session_state.db.get(item_id='home_store').get('value', [])
        price_data = data_for_store_from_db(store=home_store, data_type='price')

        # Get items_list
        data_dict = st.session_state.db.get(item_id='items_list', default={})
        if data_dict:
            data=data_dict.get('value', [])

            options = [d['ItemCode'] for d in price_data]

            edited_data = st.data_editor(
                data=data,
                column_order=('item_code', 'quantity'),
                column_config={
                    'item_code': st.column_config.SelectboxColumn(
                        label='Product',
                        options=sorted(options, key=int),
                        format_func=lambda x: f"{x} - {next(d.get('ItemName') or d.get('ItemNm')
                                                            for d in price_data if d['ItemCode'] == x)}",
                    )
                }
            )


