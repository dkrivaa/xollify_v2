import streamlit as st

from common.utilities.supermarkets import get_chain_from_code
from backend.db.crud.items import item_details
from backend.services.redis import (upstash_client, upstash_save_value, upstash_append_item,
                                    upstash_get_value, upstash_delete_key)
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector
from ui.views.stores_section import stores_section_element


def render():
    """ Function to render home page """
    # Reset selectors (after a store has been selected)
    if st.session_state.get('reset_selectors_flag', False):
        st.session_state['chain_selector'] = None
        st.session_state['store_selector'] = None
        st.session_state['reset_selectors_flag'] = False

    logo()

    # Top navigation menu
    navigation_selection = navigation_section()
    st.space()

    if navigation_selection == 1:
        stores_section_element()



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
            data = [{**d, 'delete': False, 'chain': get_chain_from_code(d['chain_code']).alias}
                    for d in data]
            edited_data = st.data_editor(data=data, width='stretch',
                                         column_order=['chain', 'delete'],
                                         column_config={
                               'chain': st.column_config.TextColumn(label='Chain'),
                               'chain_code': st.column_config.TextColumn(label='Chain Code'),
                               'store_code': st.column_config.TextColumn(label='Store'),
                               'delete': st.column_config.CheckboxColumn(label='Delete',
                                                                         width='small',)}
                                         )










if __name__ == "__main__":
    render()