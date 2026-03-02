import streamlit as st

from backend.db.crud.items import item_details
from backend.services.redis import upstash_client, upstash_save_value, upstash_get_value, upstash_delete_key
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector


def render():
    """ Function to render home page """
    logo()
    st.divider()

    # Top navigation menu
    navigation_selection = navigation_section()

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
    with st.container():
        # Show chain selector
        chain_code = chain_selector()
        if chain_code:
            # Show store selector for selected chain
            store_code = store_selector(chain_code)




if __name__ == "__main__":
    render()