import streamlit as st


def get_database_url():
    """ Get the supabase database url """
    return st.secrets['DATABASE_URL']


print(get_database_url())