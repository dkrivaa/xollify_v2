import streamlit as st

from ui.elements.static import logo
from ui.utilities.results import organize_shoppinglists, total_cost_per_store, best_cost_for_k_stores


def render():
    """ Main function to render results page """
    logo()
    st.divider()
    st.space()

    stores = st.session_state.db.get('stores').get('value', [])
    shoppinglists = organize_shoppinglists()

    for store in stores:
        st.write(store)
        st.write(total_cost_per_store(shoppinglists, store))



    best_combo, best_total, best_plan = best_cost_for_k_stores(shoppinglists, 2)

    st.write('best_combo')
    st.write(best_combo)

    st.write('best_total')
    st.write(best_total)

    st.write('best_plan')
    st.write(best_plan)



if __name__ == "__main__":
    render()