import streamlit as st

from ui.utilities.workflow import enforce_workflow


def lists_section_element():
    """ Section to show shoppinglist section """
    # Checks of user selections (stores and home store) and data
    enforce_workflow()

    tab1, tab2, tab3 = st.tabs([":green[Upload Shopping List]",
                                ":green[Make / Add to Shopping List]",
                                ":green[See Items in List]"])
