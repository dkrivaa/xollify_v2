import streamlit as st

from ui.elements.static import logo


def render():
    """ Main function to render results page """
    logo()
    st.divider()
    st.space()

    stores = st.session_state.get(item_id='stores').get('value')
    store_keys = [f"{s['chain_code']}_{s['store_code']}_shoppinglist" for s in stores]
    for key in store_keys:
        st.write(st.session_state.get(item_id=key))


if __name__ == "__main__":
    render()