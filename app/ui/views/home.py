import streamlit as st

from backend.db.crud.items import item_details
from backend.services.redis import (upstash_client, upstash_save_value, upstash_append_item,
                                    upstash_get_value, upstash_delete_key)
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector


def render():
    """ Function to render home page """
    logo()

    st.write(st.session_state)
    # Top navigation menu
    navigation_selection = navigation_section()
    st.space()

    if navigation_selection == 1:
        stores_section()



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


def stores_section():
    """ Section to select stores of interest """
    with st.container(border=True):

        tab1, tab2 = st.tabs(['Select Store', 'Manage Selected Stores'])

        with tab1:
            # Show chain selector
            chain_code = chain_selector()
            if chain_code:
                # Show store selector for selected chain
                store_code = store_selector(chain_code)
                if store_code:
                    # Add store to session_state and upstash
                    add_store = st.button(label='Add Store',
                                          icon=':material/add_business:',
                                          icon_position='left',
                                          width='stretch')
                    if add_store:
                        redis_client = upstash_client
                        upstash_append_item(redis_client, 'stores', {'chain_code': chain_code,
                                                                     'store_code': store_code})





if __name__ == "__main__":
    render()