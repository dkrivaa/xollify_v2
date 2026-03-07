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
from common.bootstrap import initialize_backend
initialize_backend()

# st.set_page_config - Set the configuration of the Streamlit page
# # Get screen size
# screen_width = streamlit_js_eval(js_expressions="window.innerWidth", key="sw")
# # Define layout for mobile ("wide") and desktop ("centered")
# layout: Literal["centered", "wide"] = "wide" if (screen_width and screen_width < 768) else "centered"
st.set_page_config(
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize upstash and assign user unique sid
from backend.services.redis import init_session
init_session()

# Initialize IndexedDB
from backend.services.indexeddb_session import SessionIndexedDB
if "db" not in st.session_state:
    st.session_state.db = SessionIndexedDB("XollifyDB", "data")
    st.session_state.db.init()

st.session_state.db.recover_if_needed()



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



