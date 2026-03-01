import streamlit as st


from common.upstash.redis_service import get_redis_client
from backend.db.crud.items import item_details
from backend.services.redis import redis_client_params, upstash_save_value, upstash_get_value
from ui.elements.static import logo
from ui.elements.dynamic import chain_selector, store_selector


def render():
    """ Function to render home page """
    logo()

    st.divider()

    upstash_url, upstash_token = redis_client_params()
    redis_client = get_redis_client(upstash_url, upstash_token)
    upstash_save_value(redis_client, 'test', 'the value')

    chain = chain_selector()
    if chain:
        store = store_selector(chain)

    val = upstash_get_value(redis_client, 'test')
    st.write(val)




if __name__ == "__main__":
    render()