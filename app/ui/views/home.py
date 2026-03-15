import streamlit as st

from ui.elements.static import logo
from ui.elements.dynamic import lang


def render():
    """ Main func to render page """
    logo()
    language = 'english'
    icon_position = 'left' if language == 'english' else 'right'

    st.divider()
    st.space()

    label1 = {'english': 'Check Product Price & Promos',
              'hebrew': 'מחיר מוצר ומבצעים'}
    if st.button(label=label1[language],
                 type='secondary',
                 width='stretch',
                 icon=':material/add_shopping_cart:',
                 icon_position=icon_position,
                 key='info_key'):
        st.session_state['title'] = 'Before Getting Product Price and Promos'
        st.switch_page('ui/views/home_store.py')

    st.space()

    label2 = {'english': 'Compare Cost of Shopping List',
              'hebrew': 'השוואת עלות רשימת קניות'}
    if st.button(label=label2[language],
                 type='secondary',
                 width='stretch',
                 icon=':material/list:',
                 icon_position=icon_position,
                 key='plan_key'):
        st.session_state['title'] = 'Before Comparing Cost of Shopping List'
        st.switch_page('ui/views/home_store.py')


if __name__ == "__main__":
    render()