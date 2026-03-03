import streamlit as st


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
    home_store = st.radio(label='Select',
                          label_visibility='hidden',
                          options=[f"{d['chain_code']}_{d['store_code']}" for d in current],
                          format_func=lambda x: next(f"{d['chain_alias']} - {d['store_name']}"
                                                     for d in current
                                                     if d['chain_code'] == x.split('_')[0]
                                                     if d['store_code'] == x.split('_')[1]),
                          index=None
                          )
    # If user selected - show button
    if home_store:
        if st.button(label='Submit', width='stretch'):
            # if submit - enter selection into session_state and indexedDB
            st.session_state.db.put(item_id='home_store', value=home_store)
            return


