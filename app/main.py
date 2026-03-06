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


# STARTUP CODE TO RUN APP ###########
# Initialize all chains
from common.bootstrap import initialize_backend
initialize_backend()

# st.set_page_config - Set the configuration of the Streamlit page
st.set_page_config(
    layout="wide",
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

# Pills
st.markdown("""
<style>

/* Pills container */
div[data-testid="stPills"] {
    flex-wrap: nowrap !important;
    overflow-x: auto;
    gap: 0.4rem;
    padding-bottom: 0.2rem;
}

/* Individual pills */
div[data-testid="stPills"] button {
    flex: 0 0 auto;
    border-radius: 20px;
    padding: 6px 14px;
    font-weight: 500;
    white-space: nowrap;
}

/* Hide scroll bar (mobile friendly) */
div[data-testid="stPills"]::-webkit-scrollbar {
    display: none;
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



