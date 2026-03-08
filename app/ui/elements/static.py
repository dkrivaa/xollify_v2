import streamlit as st


def logo():
    """ Logo at top of all pages """
    st.title(body=':orange[:material/attach_money: Xollify]',
             width='stretch',
             text_alignment='center')

    st.divider()


def explanation():
    """ Popover with explanation of app """
    with st.popover(label='Learn more', type='tertiary', ):
        st.subheader(body=':orange[Xollify]', text_alignment='center')


def no_stores_selected():
    """ Show message if no stores are selected """
    with st.container(border=True):
        st.subheader(body=':material/error: No stores selected',
                     width='stretch',
                     text_alignment='center')
        st.markdown(body='Please Select Store/s to continue',
                    width='stretch',
                    text_alignment='center')
