import streamlit as st

from ui.elements.dynamic import home_store_selector


@st.dialog(title=':material/home: Select Your "Home Store"', dismissible=False)
def get_home_store():
    """ Dialog function to get 'Home Store """
    st.markdown(body='The "Home Store" is used to select items for your shopping and should represent where you normally shops',
                text_alignment='center')

    try:
        current = st.session_state.db.get(item_id='stores')['value']
        if current is None:
            current = []
    except TypeError as e:
        # TypeError -> current is None =>
        current = []
    # Radio to display selected stores
    home_store = home_store_selector()
    # If user selected - show button
    if home_store:
        if st.button(label='Submit', width='stretch'):
            # if submit - enter selection into session_state and indexedDB
            st.session_state.db.put(item_id='home_store', value=home_store)
            st.rerun()


