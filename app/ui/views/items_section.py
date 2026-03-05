import streamlit as st

from common.core.super_class import SupermarketChain
from ui.utilities.workflow import enforce_workflow
from ui.utilities.items import data_for_store_from_db, relevant_promos_for_item, get_item_dict_from_db
from ui.utilities.general import sorted_stores
from ui.elements.dynamic import item_selector, price_element, promo_element
from ui.elements.dialogs import alternative_dialog


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
            # Temp store key
            store_key = f"{store['chain_code']}_{store['store_code']}"

            # Get price data for store
            price_data = data_for_store_from_db(store=store)



            # Get item dict from price data for selected item
            item_dict = next((d for d in price_data if d['ItemCode'] == item), {})

            # Default effective item code for this store
            effective_item = item  # default to original

            if not item_dict:
                # Check if user already selected an alternative for this store
                alt_key = f"alt_{store_key}_{item}"
                alt_item = st.session_state.db.get(alt_key)

                if alt_item:
                    # Use alternative item selected in previous rerun
                    effective_item = alt_item
                    item_dict = next((d for d in price_data if d['ItemCode'] == alt_item), {})
                else:
                    # Flag to run alternative dialog is raised
                    flag = st.session_state.db.get(item_id='alternative_flag')
                    if flag and flag.get('value', False):
                        # Get item dict from supabase db
                        original_dict = get_item_dict_from_db(item)
                        alt_key = f"alt_{store_key}_{item}"
                        # Show alternative dialog
                        alternative_dialog(price_data, original_dict, store, alt_key)
                        st.stop()  # Avoid continued code execution in current run
                    else:
                        # No alternative yet — raise flag to show alternative dialog
                        st.session_state.db.put(item_id='alternative_flag', value=True)
                        st.rerun()

            # Display price element
            price_element(item=effective_item, item_details=item_dict, store=store)

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
                else:
                    st.info('No promotions found for this item')

            st.divider()




    st.write(st.session_state)







