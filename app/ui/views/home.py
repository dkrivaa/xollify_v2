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
    st.button(label='Test',
              type='tertiary',
              width='stretch',
              icon=':material/arrow_forward:',
              icon_position='right',
              key='ter')


if __name__ == "__main__":
    render()