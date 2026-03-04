import streamlit as st

from ui.utilities.workflow import enforce_workflow



def items_section_element():
    """ Section to show item details """
    # Checks of user selections and data
    enforce_workflow()
    # END OF LOGICAL TESTS ################

    # Get price and promo data for selected stores and enter into session_state and indexedDB
    # Automatically checks if store data already entered and removes stale store data


    st.write(st.session_state)







