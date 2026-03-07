import streamlit as st

from ui.utilities.general import remove_home_store_from_db
from ui.elements.dynamic import chain_selector, store_selector


def make_data_for_editor(data: list[dict]):
    """ Make the data ready for insert into data_editor by adding delete column """
    return [{**d, 'delete': False, } for d in data]


def reorganize_data(edited_data: list[dict]):
    """ Reorganize data after edit by user """
    keys_to_remove = ["delete", ]
    # Remove keys and remove rows with delete=True
    stores = [
        {k: v for k, v in d.items() if k not in keys_to_remove}
        for d in edited_data
        if not d.get("delete", False)
    ]
    # Remove home store if removed from selected stores
    remove_home_store_from_db(stores=stores)
    # Save updated stores data to session_state and indexedDB
    st.session_state.db.put(item_id='stores', value=stores)
    # Rerun app
    st.rerun()


def stores_section_element():
    """ Section to select stores of interest """
    with st.container(border=True):
        # Define tabs
        tab1, tab2 = st.tabs(['Select Store', 'Selected Stores'])

        # Select stores
        with tab1:
            # Show chain selector
            chain_code, chain_alias = chain_selector()
            if chain_code:
                # Show store selector for selected chain
                store_code, store_name = store_selector(chain_code)
                # if store_code:
                # Add store to session_state and upstash
                if st.button(label='Add Store',
                             icon=':material/add_business:',
                             icon_position='left',
                             width='stretch',
                             key='add_store_button',
                             disabled=not store_code):
                    # Enter new store into session_state and indexedDB
                    try:
                        current = st.session_state.db.get(item_id='stores')['value']
                        if not current:
                            current = []
                    except TypeError as e:
                        # TypeError -> current is None =>
                        current = []
                    # Add new store if not in list already
                    new_store = {'chain_code': chain_code,
                                 'chain_alias': chain_alias,
                                 'store_code': store_code,
                                 'store_name': store_name}
                    if new_store not in current:
                        current.append(new_store)
                        # Enter all stores into session_state and indexedDB
                        st.session_state.db.put(item_id='stores', value=current)
                        # Delete present home store
                        st.session_state.db.delete(item_id='home_store')
                        # Reset flag to clear select boxes
                        st.session_state['reset_selectors_flag'] = True
                        st.rerun()

        # Manage stores selected
        with tab2:
            data = st.session_state.db.get(item_id='stores', default=[])

            if data:
                organized_data = make_data_for_editor(data.get('value'))
                edited_data = st.data_editor(
                    data=organized_data, width='stretch',
                    column_order=['chain_alias', 'store_name', 'delete'],
                    column_config={'chain_alias': st.column_config.TextColumn(label='Chain', disabled=True),
                                   'store_name': st.column_config.TextColumn(label='Store Name', disabled=True),
                                   'chain_code': st.column_config.TextColumn(label='Chain Code'),
                                   'store_code': st.column_config.TextColumn(label='Store'),
                                   'delete': st.column_config.CheckboxColumn(label='Delete', width='small',)
                                   }
                )

                if st.button(label='Update Data',
                             icon=':material/refresh:',
                             icon_position='left',
                             width='stretch'):
                    reorganize_data(edited_data)

