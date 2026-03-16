import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector, lang
from ui.utilities.stores import add_store_to_session_state_indexeddb


def render():
    """ Main func to render page """
    logo()
    st.divider()
    st.space()

    # Add title to page
    # if 'title' in st.session_state:
    #     st.subheader(st.session_state.get('title'))

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body='Just a few questions to get the relevant data:')
        # Show question according to activity selected on home page
        if st.session_state.get('activity') == 'info':
            st.markdown(body=':blue[Where are you shopping?]')
        elif st.session_state.get('activity') == 'plan':
            st.markdown(body=':blue[Where do you normally shop?]')

        # Show chain selector
        chain_code, chain_alias = chain_selector()
        if chain_code:
            # Show store selector for selected chain
            store_code, store_name = store_selector(chain_code)
            # Add home store to session_state
            if st.button(label='Add "Home Store"',
                         icon=':material/add_business:',
                         icon_position='left',
                         width='stretch',
                         key='add_home_store_button',
                         disabled=not store_code):
                # Enter new store into session_state and indexedDB
                add_store_to_session_state_indexeddb(chain_code, chain_alias, store_code,
                                                     store_name, home_store=True)
    #             st.session_state._navigate_to_other_stores = True
    #
    # if st.session_state.get("_navigate_to_other_stores"):
    #     # del st.session_state["_navigate_to_other_stores"]
    #     # Forward to other stores selection
    #     st.switch_page('ui/views/other_stores.py')


if __name__ == "__main__":
    render()

