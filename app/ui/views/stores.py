import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import lang


def render():
    """ Main func to render page """
    logo()
    language, icon_position = lang()
    st.divider()
    st.space()


if __name__ == "__main__":
    render()

