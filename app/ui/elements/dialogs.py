import streamlit as st

from backend.services.async_runner import run_async
from backend.agent.alternative_product import get_alternatives
from ui.elements.dynamic import home_store_selector


@st.dialog(title=':material/home: Select Your "Home Store"', dismissible=False)
def get_home_store():
    """ Dialog function to get 'Home Store """
    st.markdown(body='The "Home Store" is used to select items for your shopping '
                     'and should represent where you normally shop',
                text_alignment='center')

    try:
        stores = st.session_state.db.get(item_id='stores')['value']
        if not stores:
            stores = []
    except TypeError as e:
        # TypeError -> current is None =>
        stores = []
    # Radio to display selected stores
    home_store = home_store_selector(stores=stores)
    # If user selected - show button
    if home_store:
        if st.button(label='Submit', width='stretch'):
            # if submit - enter selection into session_state and indexedDB
            st.session_state.db.put(item_id='home_store', value=home_store)
            st.rerun()


@st.dialog(title=':material/compare_arrows: Item not found')
def alternative_dialog(price_data: list[dict], input_dict: dict, store: dict, alt_key: str):
    """
    Dialog to get alternative product
    Params:
        price_data - price_data for store without original item
        input_dict - item dict of original item - the product that has to be replaced
        store - the store dict for store that needs alternative item
        alt_key - key to store the alternative in session_state and indexedDB
    """
    # Get alternative items
    alternatives = run_async(get_alternatives, all_products=price_data, input_product=input_dict)

    with st.form(key='Alternative'):
        st.write('Suggested Alternatives')
        alt_item = st.radio(label='Select',
                            options=[d['ItemCode'] for d in alternatives],
                            format_func=lambda x: (
                               lambda d: f'₪{float(d["ItemPrice"]):.2f} - {d.get("ItemName") or d.get("ItemNm")}')
                                        (next(d for d in alternatives if d["ItemCode"] == x)),
                            index=None,
                            )



        submit = st.form_submit_button('Submit', disabled=not alt_item)

    if submit:
        # Enter selected item
        st.session_state.db.put(item_id=alt_key, value=alt_item)

        # Reset flag to show alternative dialog
        st.session_state.db.put(item_id='alternative_flag', value=False)

        st.rerun()



