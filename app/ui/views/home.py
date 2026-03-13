import streamlit as st

from ui.elements.static import logo


def render():
    """ Main func to render page """
    logo()

    language = 'hebrew'
    icon_position = 'left' if language == 'english' else 'right'

    label1 = {'english': 'Info - Product Price & Promos',
              'hebrew': 'מידע על מוצר - מחיר ומבצעים'}

    st.button(label=label1['english'],
              type='secondary',
              width='stretch',
              icon=':material/add_shopping_cart:',
              icon_position=icon_position,
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