import streamlit as st

from ui.elements.static import logo
from ui.utilities.results import organize_shoppinglists, total_cost_per_store, best_cost_for_k_stores


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
    best_combo, best_total, best_plan = best_cost_for_k_stores(shoppinglists, 1)

    tab1, tab2, tab3 = st.tabs(['Total per Store', 'Best Plan', 'Later'])

    with tab1:

        for store in stores:
            total = total_cost_per_store(shoppinglists, store)

            st.metric(label=f":blue[{store['chain_alias']} - {store['store_name']}]",
                      value=f"₪ {total}",
                      delta=":green[Best Price]" if total - best_total == 0 else f"₪ {(total - best_total):.2f}",
                      delta_color='inverse',
                      width='stretch')





    st.write('best_combo')
    st.write(best_combo)

    st.write('best_total')
    st.write(best_total)

    st.write('best_plan')
    st.write(best_plan)



if __name__ == "__main__":
    render()