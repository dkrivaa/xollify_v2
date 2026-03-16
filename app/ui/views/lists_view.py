import streamlit as st

from ui.elements.static import logo
from common.core.super_class import SupermarketChain
from ui.utilities.workflow import WorkflowStep, enforce_workflow
from ui.utilities.items import (data_for_store_from_db, relevant_promos_for_item,
                                get_item_dict_from_db, get_alternative_item)
from ui.utilities.general import sorted_stores
from ui.elements.dynamic import item_selector, price_element, promo_element


def render():
    """ The main function to display shoppinglist page """
    logo()
    st.divider()
    st.space()

    # Check all in workflow, incl. getting data for stores
    enforce_workflow()

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body=':blue[All ready!!]')


if __name__ == "__main__":
    render()