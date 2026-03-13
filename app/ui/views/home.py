import streamlit as st

from ui.elements.static import logo


def render():
    """ Main func to render page """
    logo()

    st.button(label='Test',
              type='tertiary',
              width='stretch')


if __name__ == "__main__":
    render()