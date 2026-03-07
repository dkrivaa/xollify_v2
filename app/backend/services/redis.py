import streamlit as st
import uuid

from common.upstash.redis_service import get_redis_client
from common.upstash.redis_service import (get_redis_client, save_to_redis,
                                          get_from_redis, delete_from_redis)


def init_session():
    """
    Assign UUID to user session if not already assigned.
    The user session is used to identify user data in upstash.
    """
    # if "sid" not in st.query_params:
    #     st.query_params["sid"] = str(uuid.uuid4())
    #     st.rerun()
    # return st.query_params["sid"]
    st.write(f"query_params in init: {dict(st.query_params)}")
    if "sid" not in st.query_params:
        st.write("sid NOT FOUND - generating new one")
        st.query_params["sid"] = str(uuid.uuid4())
        st.rerun()
    return st.query_params["sid"]


def redis_client_params():
    """ Get the st.secrets (UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN) to get redis client """
    upstash_url = st.secrets['UPSTASH_REDIS_REST_URL']
    upstash_token = st.secrets['UPSTASH_REDIS_REST_TOKEN']
    # Return redis client params
    return upstash_url, upstash_token


def upstash_client():
    """ Function to return redis client using streamlit secrets """
    # Get params for redis client
    upstash_url, upstash_token = redis_client_params()
    # Return redis client
    return get_redis_client(upstash_url, upstash_token)


def upstash_save_value(redis_client, key, value):
    """Save to both session_state and Redis."""
    # Get sid (user) param
    sid = st.query_params["sid"]
    # Set the session_state key value
    st.session_state[key] = value
    # Set the upstash redis value
    save_to_redis(redis_client, sid, key, value)


def upstash_append_item(redis_client, key, item):
    """ Append item to session_state and upstash """
    # Get sid (user) param
    sid = st.query_params['sid']
    # Get the current list for key from session_state or from upstash
    current = upstash_get_value(redis_client, key, default=[])
    if current is None:
        current = []
    if item not in current:
        # Append to current list
        current.append(item)
        # Set the session_state key value to updated list, incl appended item
        st.session_state[key] = current
        # Set the upstash key value to updated list, incl appended item
        save_to_redis(redis_client, sid, key, current)


def upstash_get_value(redis_client, key, default=None):
    """Get from session_state, falling back to Redis if not present."""
    # If key not in session_state
    if key not in st.session_state:
        # Get sid (user) param
        sid = st.query_params["sid"]
        # Get from redis
        value = get_from_redis(redis_client, sid, key, default)
        # If get_from_redis returned None but default was a list,
        # ensure the default is used.
        if value is None:
            value = default
        # Set session_state
        st.session_state[key] = value

    return st.session_state[key]


def upstash_delete_key(redis_client, key):
    """ Delete key from upstash and st.session_state """
    # Get sid (user) param
    sid = st.query_params["sid"]
    # If key in session_state - delete key
    if key in st.session_state:
        del st.session_state[key]
    # Delete key from upstash
    delete_from_redis(redis_client, sid, key)

