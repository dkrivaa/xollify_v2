import streamlit as st


def logo():
    """ Logo at top of all pages """
    return st.title(body=':orange[:material/attach_money: Xollify]',
                    width='stretch',
                    text_alignment='center')
