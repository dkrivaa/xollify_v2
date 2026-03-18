import streamlit as st

from ui.elements.static import logo
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
                      delta="" if total - best_total_1 == 0 else f"₪ {(total - best_total_1):.2f}",
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
            for entry in data:
                store = from_key_to_store(entry['id'], stores)
                item = entry['value'][i]  # get item at index i

                st.write(f":blue[{store['chain_alias']} - {store['store_name']}]")
                st.write(item['item_name'])
                st.write(f"₪ {float(item['item_price']):.2f}")
            st.divider()

        st.write(organize_shoppinglists())


if __name__ == "__main__":
    render()