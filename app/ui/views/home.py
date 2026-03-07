import streamlit as st

from common.utilities.supermarkets import get_chain_from_code
from backend.db.crud.items import item_details
from backend.services.redis import (upstash_client, upstash_save_value, upstash_append_item,
                                    upstash_get_value, upstash_delete_key)
from ui.utilities.general import apply_responsive_layout
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector
from ui.views.stores_section import stores_section_element
from ui.views.items_section import items_section_element


def render():
    """ Function to render home page """
    # Apply layout
    # apply_responsive_layout()

    # Reset selectors (after a store has been selected)
    if st.session_state.get('reset_selectors_flag', False):
        st.session_state['chain_selector'] = None
        st.session_state['store_selector'] = None
        st.session_state['reset_selectors_flag'] = False

    # Add logo at top of page
    logo()

    # st.write(st.session_state.db.get_all())
    # Navigation menu
    navigation_selection = navigation_section()
    st.space()

    if not navigation_selection:
        with st.container():
            st.write('More Test with container')

    else:

        if navigation_selection == 1:
            stores_section_element()
        if navigation_selection == 2:
            items_section_element()


def navigation_section():
    """ Navigation section at top of page """
    with st.container():
        pills_map = {
            1: ':material/add_business: Select Stores',
            2: ':material/add_shopping_cart: Compare Items',
            3: ':material/list: Shopping List'
        }

        section_selection = st.pills(label='Set up system',
                                     label_visibility='hidden',
                                     options=[k for k, v in pills_map.items()],
                                     format_func=lambda x: pills_map[x],
                                     default=None,
                                     width='stretch',
                                     key='nav_key')

        return section_selection


if __name__ == "__main__":
    render()