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
              icon=':material/arrow_right_alt:',
              icon_position='right',
              key='sec')
    st.button(label='Test',
              type='tertiary',
              width='stretch',
              icon=':material/arrow_right_alt:',
              icon_position='right',
              key='ter')

    st.page_link(page='ui/views/home_old.py',
                 label='Test',
                 width='stretch',
                 icon=':material/arrow_right_alt:',
                 icon_position='right',
                 )


if __name__ == "__main__":
    render()