import streamlit as st

from common.utilities.supermarkets import get_chain_from_code
from backend.services.async_runner import run_async
from backend.db.crud.items import item_details
from ui.elements.static import logo


def render():
    """ Function to render home page """
    logo()

    st.divider()


if __name__ == "__main__":
    render()