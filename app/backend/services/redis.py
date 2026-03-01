import streamlit as st
import uuid

from common.upstash.redis_service import save_to_redis, get_from_redis, delete_from_redis


def init_session():
    """Assign UUID to user session if not already assigned."""
    if "sid" not in st.query_params:
        st.query_params["sid"] = str(uuid.uuid4())
        st.rerun()
    return st.query_params["sid"]


def redis_client_params():
    """ Get the st.secrets (UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN) to get redis client """
    upstash_url = st.secrets['UPSTASH_REDIS_REST_URL']
    upstash_token = st.secrets['UPSTASH_REDIS_REST_TOKEN']
    return upstash_url, upstash_token


def upstash_save_value(redis_client, key, value):
    """Save to both session_state and Redis."""
    sid = st.query_params["sid"]
    st.session_state[key] = value
    save_to_redis(redis_client, sid, key, value)


def upstash_get_value(redis_client, key, default=None):
    """Get from session_state, falling back to Redis if not present."""
    if key not in st.session_state:
        sid = st.query_params["sid"]
        st.session_state[key] = get_from_redis(redis_client, sid, key, default)
    return st.session_state[key]


def upstash_delete_key(redis_client, key):
    """ Delete key from upstash and st.session_state """
    sid = st.query_params["sid"]
    if key in st.session_state:
        del st.session_state[key]
    delete_from_redis(redis_client, sid, key)