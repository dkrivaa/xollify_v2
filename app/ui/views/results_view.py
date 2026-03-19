import streamlit as st
import math

from ui.elements.static import logo
from common.core.super_class import SupermarketChain
from ui.elements.dynamic import promo_element
from ui.utilities.items import data_for_store_from_db, relevant_promos_for_item
from ui.utilities.results import (organize_shoppinglists, total_cost_per_store, best_cost_for_k_stores,
                                  from_key_to_store)


def render():
    """ Main function to render results page """
    logo()
    st.divider()
    st.space()

    # Get list of stores
    stores = st.session_state.db.get('stores').get('value', [])
    # Organize shoppinglists
    shoppinglists = organize_shoppinglists()

    # Get the best for 1 store
    best_combo_1, best_total_1, best_plan_1 = best_cost_for_k_stores(shoppinglists, 1)

    tab1, tab2, tab3 = st.tabs(['Total per Store', 'Max Savings', 'Later'])

    with tab1:
        st.space()
        st.subheader('Total Cost')

        for store in stores:
            total = total_cost_per_store(shoppinglists, store)

            st.metric(label=f":blue[{store['chain_alias']} - {store['store_name']}]",
                      value=f"₪ {total:.2f}",
                      delta="" if math.isclose(total, best_total_1, rel_tol=1e-9, abs_tol=1e-9) else
                            f"₪ {(total - best_total_1):.2f}",
                      delta_color='inverse',
                      width='stretch')
            st.space()

    with tab2:
        st.space()
        st.subheader('Number of stores to visit')
        st.space()

        k = st.slider(label='Number of stores to visit',
                      label_visibility='hidden',
                      min_value=1,
                      max_value=len(stores),
                      value=1,
                      )

        st.space()

        # Get the best for k store
        best_combo, best_total, best_plan = best_cost_for_k_stores(shoppinglists, k)

        # Cost
        st.metric(label=":blue[Total Cost:]",
                  value=f"₪ {best_total:.2f}",
                  width='stretch')

        st.metric(label=":blue[Total Saving:]",
                  value=f":green[₪ {(best_total - best_total_1):.2f}]",
                  width='stretch')

        st.divider()

        st.write(':blue[What to buy where]')
        for store_key in best_combo:
            store = from_key_to_store(store_key, stores)

            with st.expander(label=f"{store['chain_alias']} - {store['store_name']}"):
                for item in best_plan[store_key]:
                    st.write(f":blue[Item - {item['item_name']}]")
                    st.write(f"Barcode - {item['item']}")
                    st.write(f"Unit price - ₪ {item['unit_price']:.2f}")
                    st.write(f"Quantity - {item['quantity']:.1f}")
                    st.subheader(f"Total cost - {item['total_price']:.2f}")

                    st.divider()

    with tab3:
        data = organize_shoppinglists()

        for i in range(len(data[0]['value'])):  # number of items in shopping list

            leading_item_code = data[0]['value'][i]['item_code']

            for entry in data:
                store = from_key_to_store(entry['id'], stores)
                item = entry['value'][i]  # get item at index i

                # Get promo data for store
                promo_data = data_for_store_from_db(store=store, data_type='promo')
                promos_for_item = relevant_promos_for_item(promo_data, item['item_code'])
                # Get chain object for relevant store
                chain = next(c for c in SupermarketChain.registry if c.chain_code == store['chain_code'])

                # for first store
                if entry == data[0]:
                    st.subheader(f"{item['item_code']} - {item['item_name']}")
                    st.write(f":blue[{store['chain_alias']} - {store['store_name']}]")
                    st.write(f"₪ {float(item['item_price']):.2f}")

                    with st.expander(label=':material/money_off: Promotions'):
                        try:
                            # Display promos
                            if promos_for_item:
                                for p in promos_for_item:
                                    promo_element(chain, p)
                            else:
                                st.info('No promotions found for this item')
                        except Exception:
                            st.info('No promotions found for this item')

                else:
                    if item['item_code'] == leading_item_code:
                        st.write(f":blue[{store['chain_alias']} - {store['store_name']}]")

                    else:
                        st.write(f":blue[{store['chain_alias']} - {store['store_name']}]")
                        st.write(f":orange[{item['item_code']} - {item['item_name']}]")
                    st.write(f"₪ {float(item['item_price']):.2f}")
                    with st.expander(label=':material/money_off: Promotions'):
                        # Display promos
                        if promos_for_item:
                            for p in promos_for_item:
                                promo_element(chain, p)
                        else:
                            st.info('No promotions found for this item')

            st.divider()


if __name__ == "__main__":
    render()