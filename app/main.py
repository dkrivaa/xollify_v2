
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
# Set page configuration for all pages in app
st.set_page_config(
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize upstash and assign user unique sid
from backend.services.redis import init_session
sid = init_session()
# Initialize all chains
from common.bootstrap import initialize_backend
initialize_backend()

# Initialize IndexedDB and db in session_state
from backend.services.indexeddb_session import SessionIndexedDB
if "db" not in st.session_state:
    st.session_state.db = SessionIndexedDB(f"XollifyDB_{sid}", "data")
    st.session_state.db.init()
    # Set flag for session_state.db
    st.session_state.db_ready = False

# Handling session_state.db not ready
if not st.session_state.db_ready:
    # Get all from browser indexedDB
    records = st.session_state.db._idb.get_all()
    # Before js resolved
    if records is None:
        st.stop()    # Stop execution. When js resolves it invokes rerun
    # js resolved - records are either [] (because new user session) and so it correctly skip the following
    # or has data (ex. after mobile lock) => gets data from indexedDB and adds to session_state
    if records:
        # Add to session_state
        for record in records:
            st.session_state.db._cache_set(record["id"], record)
    # Reset flag for session_state.db
    st.session_state.db_ready = True

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



