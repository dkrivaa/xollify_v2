import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import item_selector
from ui.utilities.workflow import enforce_workflow


def render():
    """ Function to display items page """
    logo()
    st.divider()
    st.space()

    # Check all in workflow, incl. getting data for stores
    enforce_workflow()


if __name__ == "__main__":
    render()