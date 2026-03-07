
# For streamlit cloud
import subprocess
subprocess.run(["playwright", "install", "chromium"], check=True)

# For streamlit on local
import sys
import os
import asyncio
# Fix for Windows + Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Organizing the paths so streamlit can find secrets.toml on local
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from typing import Literal


# STARTUP CODE TO RUN APP ###########
# Initialize all chains


st.set_page_config(
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize upstash and assign user unique sid
st.write("checkpoint 1")

from backend.services.redis import init_session
sid = init_session()

st.write("checkpoint 2")

from common.bootstrap import initialize_backend
initialize_backend()

st.write("checkpoint 3")



# Initialize IndexedDB
from backend.services.indexeddb_session import SessionIndexedDB
if "db" not in st.session_state:
    st.session_state.db = SessionIndexedDB(f"XollifyDB_{sid}", "data")
    st.session_state.db.init()

st.write(f"cache key: {st.session_state.db._cache_key}")
st.write(f"cache key in session_state: {st.session_state.db._cache_key in st.session_state}")
st.write(f"cache contents: {st.session_state.db._cache}")

# PAGE DEFINITIONS ###########
home_page = st.Page(
    title='Xollify',
    page='ui/views/home.py',
    icon=':material/home:',
    default=True,
)

pages = [home_page]

# RUN APP ###########
pg = st.navigation(pages=pages, position='top')
pg.run()



