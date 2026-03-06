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
# Get screen size
screen_width = streamlit_js_eval(js_expressions="window.innerWidth", key="sw")
# Define layout for mobile ("wide") and desktop ("centered")
layout: Literal["centered", "wide"] = "wide" if (screen_width and screen_width < 768) else "centered"
st.set_page_config(
    layout=layout,
    initial_sidebar_state="collapsed"
)

# Initialize upstash and assign user unique sid
from backend.services.redis import init_session
init_session()

# Initialize IndexedDB
from backend.services.indexeddb_session import SessionIndexedDB
if "db" not in st.session_state:
    st.session_state.db = SessionIndexedDB("XollifyDB", "data")

# 2. CSS across app
st.markdown("""
<style>
    .block-container { max-width: 100% !important; padding: 1rem; }

    /* This alone handles most reflow automatically */
    [data-testid="column"] {
        min-width: min(100%, 300px) !important;
        flex-wrap: wrap !important;
    }

    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
        .stButton > button { width: 100%; }
        .stDataFrame, .stTable { overflow-x: auto; }
    }
</style>
""", unsafe_allow_html=True)

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



