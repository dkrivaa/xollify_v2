import streamlit as st

from ui.elements.static import logo
from ui.utilities.results import best_cost_for_k_stores


def render():
    """ Main function to render results page """
    logo()
    st.divider()
    st.space()

    all_lists = []

    stores = st.session_state.db.get(item_id='stores').get('value')
    store_keys = [f"{s['chain_code']}_{s['store_code']}_shoppinglist" for s in stores]
    for key in store_keys:
        store_list = {k: v for k, v in st.session_state.db.get(item_id=key).items() if k != 'updated_at'}
        all_lists.append(store_list)

    best_combo, best_total, best_plan = best_cost_for_k_stores(all_lists, 2)

    st.write('best_combo')
    st.write(best_combo)

    st.write('best_total')
    st.write(best_total)

    st.write('best_plan')
    st.write(best_plan)



if __name__ == "__main__":
    render()