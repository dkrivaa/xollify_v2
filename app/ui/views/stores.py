import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import lang
from ui.views.stores_section import stores_section_element


def render():
    """ Main func to render page """
    logo()
    st.divider()
    st.space()

    with st.chat_message(name='ai', width='stretch'):
        st.markdown(body='Just a few questions:')

        stores_section_element()




if __name__ == "__main__":
    render()

