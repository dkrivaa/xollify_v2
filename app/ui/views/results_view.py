import streamlit as st

from ui.elements.static import logo


def render():
    """ Main function to render results page """
    logo()
    st.divider()
    st.space()


if __name__ == "__main__":
    render()