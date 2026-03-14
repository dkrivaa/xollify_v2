import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector, lang
from ui.views.stores_section import stores_section_element


def render():
    """ Main func to render page """
    logo()
    st.divider()
    st.space()

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body='Just a few questions:')

        st.markdown(body='Where do you normally shop?')
        # Show chain selector
        chain_code, chain_alias = chain_selector()
        if chain_code:
            # Show store selector for selected chain
            store_code, store_name = store_selector(chain_code)
            # if store_code:
            # Add store to session_state
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





if __name__ == "__main__":
    render()

