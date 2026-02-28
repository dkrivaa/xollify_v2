import streamlit as st

from common.services.supermarkets import get_chain_from_code
from backend.services.async_runner import run_async
from backend.db.crud.items import item_details


# data = run_async(test_item, item_code='7290000072753')
# st.write(data)

chain = get_chain_from_code('7290027600007')
st.write(chain.alias)