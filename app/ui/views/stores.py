import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector, lang
from ui.views.stores_section import stores_section_element


def render():
    """ Main func to render page """
    logo()
    st.divider()
    st.space()

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body='Just a few questions:')

        st.markdown(body='Where do you normally shop?')
        # Show chain selector
        chain_code, chain_alias = chain_selector()
        if chain_code:
            # Show store selector for selected chain
            store_code, store_name = store_selector(chain_code)





if __name__ == "__main__":
    render()

