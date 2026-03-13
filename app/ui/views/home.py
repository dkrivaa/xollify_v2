import streamlit as st

from ui.elements.static import logo


def render():
    """ Main func to render page """
    st.logo(image='https://www.google.com/imgres?q=shufersal&imgurl=https%3A%2F%2Fmma.prnewswire.com%2Fmedia%2F1592092%2FShufersal_Logo.jpg%3Fp%3Dfacebook&imgrefurl=https%3A%2F%2Fwww.prnewswire.com%2Fil%2Fnews-releases%2Fshufersal-reports-second-quarter-and-first-half-2021-financial-results-301353115.html&docid=e5BSHVC6CfRxwM&tbnid=Ot0TNKJaiy8BnM&vet=12ahUKEwiax5TZip2TAxXBg_0HHdxtHlkQnPAOegQIGxAB..i&w=2700&h=1414&hcb=2&ved=2ahUKEwiax5TZip2TAxXBg_0HHdxtHlkQnPAOegQIGxAB')
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
                 icon=':material/arrow_right_alt:',
                 icon_position='right',
                 )


if __name__ == "__main__":
    render()