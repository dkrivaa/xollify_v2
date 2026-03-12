import streamlit as st

from common.core.super_class import SupermarketChain
from ui.utilities.workflow import WorkflowStep, enforce_workflow
from ui.utilities.items import (data_for_store_from_db, relevant_promos_for_item,
                                get_item_dict_from_db, get_alternative_item)
from ui.utilities.general import sorted_stores
from ui.elements.dynamic import item_selector, price_element, promo_element
from ui.elements.dialogs import alternative_dialog


def items_section_element():
    """ Section to show item details """
    # Checks of user selections (stores and home store) and data
    # check stores exist
    enforce_workflow(required=WorkflowStep.NO_STORES)

    # Set temp home store
    stores = st.session_state.db.get(item_id='stores').get('value', [])
    if len(stores) == 1:
        st.session_state['temp_home_store'] = stores[0]

    # Check all in workflow, incl. getting data for stores
    enforce_workflow()

    # Get data for item selector (from home store)
    store = st.session_state.db.get('home_store').get('value', [])

    price_data = data_for_store_from_db(store=store)
    # Display item selector
    item = item_selector(price_data=price_data)
    do_alternatives = st.toggle(label='When item N/A, select alternative item', value=False)
    st.space()

    # Show results
    if item:
        # Sort stores (home store first)
        stores = sorted_stores()

        for store in stores:
            # Temp store key
            store_key = f"{store['chain_code']}_{store['store_code']}"

            # Get price data for store
            price_data = data_for_store_from_db(store=store)

            # Get item dict from price data for selected item
            item_dict = next((d for d in price_data if d['ItemCode'] == item), {})

            # Default effective item code for this store
            effective_item = item  # default to original

            # Alternative items
            if do_alternatives:

                if not item_dict:
                    # Get alternative data from dialog
                    effective_item, quantity, item_dict = get_alternative_item(store=store, item=item)

            # Display price element
            price_element(item=effective_item, item_details=item_dict, store=store, delta=effective_item != item)

            with st.expander(label=':material/money_off: Promotions'):
                # Get promo data for store
                promo_data = data_for_store_from_db(store=store, data_type='promo')
                promos_for_item = relevant_promos_for_item(promo_data, effective_item)
                # Get chain object for relevant store
                chain = next(c for c in SupermarketChain.registry if c.chain_code == store['chain_code'])
                # Display promos
                if promos_for_item:
                    for p in promos_for_item:
                        promo_element(chain, p)
                elif not do_alternatives and effective_item != item:
                    st.info('No promotions found for this item')
                else:
                    st.info('No promotions found for this item')

            st.divider()









