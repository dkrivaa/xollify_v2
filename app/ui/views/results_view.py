import streamlit as st

from ui.elements.static import logo
from ui.utilities.results import organize_shoppinglists, best_cost_for_k_stores


def render():
    """ Main function to render results page """
    logo()
    st.divider()
    st.space()

    shoppinglists = organize_shoppinglists()

    best_combo, best_total, best_plan = best_cost_for_k_stores(shoppinglists, 2)

    st.write('best_combo')
    st.write(best_combo)

    st.write('best_total')
    st.write(best_total)

    st.write('best_plan')
    st.write(best_plan)



if __name__ == "__main__":
    render()