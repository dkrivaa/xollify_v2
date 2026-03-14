import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector, lang
from ui.utilities.stores import add_store_to_session_state_indexeddb


def render():
    """ Main func to render page """
    logo()
    st.divider()
    st.space()

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body='Just a few questions:')

        st.markdown(body=':blue[Where do you normally shop?]')
        # Show chain selector
        chain_code, chain_alias = chain_selector()
        if chain_code:
            # Show store selector for selected chain
            store_code, store_name = store_selector(chain_code)
            # Add store to session_state
            if st.button(label='Add "Home Store"',
                         icon=':material/add_business:',
                         icon_position='left',
                         width='stretch',
                         key='add_store_button',
                         disabled=not store_code):
                # Enter new store into session_state and indexedDB
                add_store_to_session_state_indexeddb(chain_code, chain_alias, store_code,
                                                     store_name, home_store=True)





if __name__ == "__main__":
    render()

