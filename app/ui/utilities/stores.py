import streamlit as st


def add_store_to_session_state_indexeddb(chain_code: str,
                                         chain_alias: str,
                                         store_code: str,
                                         store_name: str,
                                         home_store: bool = False):
    """ Function to enter selected store into session_state and indexedDB """
    if home_store:
        store = {'chain_code': chain_code,
                 'chain_alias': chain_alias,
                 'store_code': store_code,
                 'store_name': store_name}
        st.session_state.db.put(item_id='home_store', value=store)

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
