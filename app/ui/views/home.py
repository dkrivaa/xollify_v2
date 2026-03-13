import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import lang


def render():
    """ Main func to render page """
    logo()
    language, icon_position = lang()
    st.divider()

    label1 = {'english': 'Info - Product Price & Promos',
              'hebrew': 'מידע על מוצר - מחיר ומבצעים'}
    st.button(label=label1[language],
              type='secondary',
              width='stretch',
              icon=':material/add_shopping_cart:',
              icon_position=icon_position,
              key='info_key')

    st.space()

    label2 = {'english': 'Plan - Compare Cost of Shopping List',
              'hebrew': 'תכנון - השוואת עלות רשימת קניות'}
    st.button(label=label2[language],
              type='secondary',
              width='stretch',
              icon=':material/list:',
              icon_position=icon_position,
              key='plan_key')


if __name__ == "__main__":
    render()