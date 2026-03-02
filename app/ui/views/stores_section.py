import streamlit as st

from common.utilities.supermarkets import get_chain_from_code
from common.db.crud.stores import get_store_name
from backend.services.async_runner import run_async
from backend.services.redis import (upstash_client, upstash_save_value, upstash_append_item,
                                    upstash_get_value, upstash_delete_key)
from ui.elements.dynamic import chain_selector, store_selector


def make_data_for_editor(data: list[dict]):
    """ Make the data ready for insert into data_editor by adding relevant columns """
    DATABASE_URL = st.secrets['DATABASE_URL']

    return [{**d, 'delete': False, 'chain': get_chain_from_code(d['chain_code']).alias,
             'store_name': run_async(get_store_name, DATABASE_URL=DATABASE_URL,
                                     chain_code=d['chain_code'], store_code=d['store_code'])} for d in data]


def stores_section_element():
    """ Section to select stores of interest """
    with st.container(border=True):
        # Define tabs
        tab1, tab2 = st.tabs(['Select Store', 'Selected Stores'])

        # Select stores
        with tab1:
            # Show chain selector
            chain_code = chain_selector()
            if chain_code:
                # Show store selector for selected chain
                store_code = store_selector(chain_code)
                if store_code:
                    # Add store to session_state and upstash
                    if st.button(label='Add Store',
                                 icon=':material/add_business:',
                                 icon_position='left',
                                 width='stretch',
                                 key='add_store_button'):
                        redis_client = upstash_client()
                        upstash_append_item(redis_client, 'stores', {'chain_code': chain_code,
                                                                     'store_code': store_code})
                        st.session_state['reset_selectors_flag'] = True
                        st.rerun()

        # Manage stores selected
        with tab2:
            redis_client = upstash_client()
            # Get stores from session_state or upstash
            data = upstash_get_value(redis_client, 'stores')
            if data:
                organized_data = make_data_for_editor(data)
                edited_data = st.data_editor(data=organized_data, width='stretch',
                                             column_order=['chain', 'delete'],
                                             column_config={
                                   'chain': st.column_config.TextColumn(label='Chain'),
                                   'chain_code': st.column_config.TextColumn(label='Chain Code'),
                                   'store_code': st.column_config.TextColumn(label='Store'),
                                   'delete': st.column_config.CheckboxColumn(label='Delete',
                                                                             width='small',)}
                                             )

