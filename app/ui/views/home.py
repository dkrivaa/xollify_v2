import streamlit as st

from ui.elements.static import logo


def render():
    """ Main func to render page """
    logo()

    st.button(label='Info - Product Price & Promos',
              type='secondary',
              width='stretch',
              icon=':material/add_shopping_cart:',
              icon_position='left',
              key='info_key')

    st.space()

    st.button(label='Plan - Compare Cost of Shopping List',
              type='secondary',
              width='stretch',
              icon=':material/list:',
              icon_position='left',
              key='plan_key')


if __name__ == "__main__":
    render()