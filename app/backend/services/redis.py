import streamlit as st
import uuid

from common.upstash.redis_service import get_redis_client, save_to_redis, get_from_redis


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


def save_value(redis, key, value):
    """Save to both session_state and Redis."""
    sid = st.query_params["sid"]
    st.session_state[key] = value
    save_to_redis(redis, sid, key, value)


def get_value(redis, key, default=None):
    """Get from session_state, falling back to Redis if not present."""
    if key not in st.session_state:
        sid = st.query_params["sid"]
        st.session_state[key] = get_from_redis(redis, sid, key, default)
    return st.session_state[key]