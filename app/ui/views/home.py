import streamlit as st



from backend.db.crud.items import item_details
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector


def render():
    """ Function to render home page """
    logo()

    st.divider()

    sid = st.query_params["sid"]
    st.write('Sid:', sid)
    chain = chain_selector()
    if chain:
        store = store_selector(chain)




if __name__ == "__main__":
    render()