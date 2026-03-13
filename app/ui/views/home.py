import streamlit as st

from ui.elements.static import logo


def render():
    """ Main func to render page """
    logo()

    st.button(label='Test',
              type='primary',
              width='stretch',
              key='pri')
    st.button(label='Test',
              type='secondary',
              width='stretch',
              key='sec')
    st.button(label='Test :material/arrow_right:',
              type='tertiary',
              width='stretch',
              key='ter')


if __name__ == "__main__":
    render()