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

        # Get the best for k store
        best_combo, best_total, best_plan = best_cost_for_k_stores(shoppinglists, k)

        st.write('Stores to visit:')
        for store_key in best_combo:
            store = from_key_to_store(store_key, stores)
            st.subheader(f"{store['chain_alias']} - {store['store_name']}")

        st.divider()

        st.metric(label="Total Cost:",
                  value=f"₪ {best_total:.2f}",
                  width='stretch')

        st.metric(label="Total Saving:",
                  value=f":green[₪ {(best_total - best_total_1):.2f}]",
                  width='stretch')

        st.divider()

        st.write('best_total')
        st.write(best_total)

        st.write('best_plan')
        st.write(best_plan)



if __name__ == "__main__":
    render()