import streamlit as st

from ui.utilities.workflow import enforce_workflow


def items_section_element():
    """ Section to show item details """
    # Checks of user selections (stores and home store) and data
    enforce_workflow()

    st.write(st.session_state)







