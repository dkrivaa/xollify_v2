import streamlit as st

from ui.utilities.workflow import enforce_workflow


def lists_section_element():
    """ Section to show shoppinglist section """
    # Checks of user selections (stores and home store) and data
    enforce_workflow()

    tab1, tab2, tab3 = st.tabs([":green[:material/upload: Upload List]",
                                ":green[:material/add_shopping_cart: Make/Add to List]",
                                ":green[:material/visibility: See List]"])


