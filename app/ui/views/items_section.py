import streamlit as st

from common.core.super_class import SupermarketChain
from ui.utilities.workflow import enforce_workflow
from ui.utilities.items import data_for_store_from_db, relevant_promos_for_item, get_item_dict_from_db
from ui.utilities.general import sorted_stores
from ui.elements.dynamic import item_selector, price_element, promo_element


def items_section_element():
    """ Section to show item details """
    # Checks of user selections (stores and home store) and data
    enforce_workflow()

    # Get data for item selector (from home store)
    store = st.session_state.db.get('home_store').get('value', [])
    price_data = data_for_store_from_db(store=store)
    # Display item selector
    item = item_selector(price_data=price_data)
    st.space()

    # Show results
    if item:
        # Sort stores (home store first
        stores = sorted_stores()

        for store in stores:
            # Get price data for store
            price_data = data_for_store_from_db(store=store)

            # Get item dict from price data for selected item
            item_dict = next((d for d in price_data if d['ItemCode'] == item), {})

            if not item_dict:
                original_dict = get_item_dict_from_db(item)
                # alternative_item_dict = function(original_dict)


            # Display price element
            price_element(item=item, item_details=item_dict, store=store)

            with st.expander(label=':material/money_off: Promotions'):
                # Get promo data for store
                promo_data = data_for_store_from_db(store=store, data_type='promo')
                promos_for_item = relevant_promos_for_item(promo_data, item)

                chain = next(c for c in SupermarketChain.registry if c.chain_code == store['chain_code'])
                if promos_for_item:
                    for p in promos_for_item:
                        promo_element(chain, p)
                else:
                    st.info('No promotions found for this item')

            st.divider()




    st.write(st.session_state)







