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

# 2. CSS across app
# st.markdown("""
# <style>
#     @media (max-width: 768px) {
#         .block-container {padding: 1rem;}
#         .stButton > button {width: 100%;}
#     }
# </style>
# """, unsafe_allow_html=True)

# 2️⃣ Global CSS (place it here)
st.markdown("""
<style>

/* Reduce overall page padding */
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* Reduce vertical spacing between elements */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.5rem;
}

/* Mobile adjustments */
@media (max-width: 768px) {

    /* Hide sidebar on phones */
    section[data-testid="stSidebar"] {
        display: none;
    }

    /* Even tighter spacing on phones */
    .block-container {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }

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



