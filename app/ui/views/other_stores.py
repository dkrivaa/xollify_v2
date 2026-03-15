import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector, lang
from ui.utilities.stores import add_store_to_session_state_indexeddb


def render():
    """ Main func to render page """
    logo()
    st.divider()
    st.space()

    message = 'Great. Added your "Home Store"'
    question = 'Do you want to add stores to compare prices?'

    # Check if flag to reset selectors (after a store has been selected)
    if st.session_state.get('reset_selectors_flag', False):
        st.session_state['chain_selector'] = None
        st.session_state['store_selector'] = None
        st.session_state['reset_selectors_flag'] = False
        # Change message and question after store has been selected
        message = 'Added the selected store'
        question = 'Do you want to add another store?'

    with st.chat_message(name='ai', width='stretch', ):
        st.markdown(body=message)
        st.markdown(body=f':blue[{question}]')

        # Show chain selector
        chain_code, chain_alias = chain_selector()
        if chain_code:
            # Show store selector for selected chain
            store_code, store_name = store_selector(chain_code)
            # Add store to session_state
            if st.button(label='Add Store',
                         icon=':material/add_business:',
                         icon_position='left',
                         width='stretch',
                         key='add_store_button',
                         disabled=not store_code):
                # Enter new store into session_state and indexedDB
                add_store_to_session_state_indexeddb(chain_code, chain_alias, store_code,
                                                     store_name, home_store=False)

                # Reset flag to clear select boxes
                st.session_state['reset_selectors_flag'] = True

        st.space()
        st.divider()

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            # Go to selected stores
            if st.button(label='See Selected Stores', width='stretch',
                         icon=':material/visibility:', icon_position='left'):
                st.switch_page('ui/views/selected_stores.py')
        with col2:
            # Forward to items or shoppinglist
            if st.button(label='Next',
                         width='stretch',
                         icon=':material/east:',
                         icon_position='right'):
                if st.session_state.get('activity') == 'info':
                    pass
                if st.session_state.get('activity') == 'plan':
                    pass



if __name__ == "__main__":
    render()