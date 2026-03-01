import streamlit as st

from backend.db.crud.items import item_details
from backend.services.redis import upstash_client, upstash_save_value, upstash_get_value, upstash_delete_key
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector


def render():
    """ Function to render home page """
    logo()

    st.divider()

    chain = chain_selector()
    if chain:
        store = store_selector(chain)



if __name__ == "__main__":
    render()