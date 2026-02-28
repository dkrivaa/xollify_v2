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

from common.bootstrap import initialize_backend


# Startup code to run the app
# Initialize all chains
initialize_backend()
st.write('hello')

# st.set_page_config - Set the configuration of the Streamlit page
st.set_page_config(
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. CSS across app
st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container {padding: 1rem;}
        .stButton > button {width: 100%;}
    }
</style>
""", unsafe_allow_html=True)

home_page = st.Page(
    title='Home',
    page='ui/views/home.py',
    icon=':material/home:',
    default=True,
)

pages = [home_page]

pg = st.navigation(pages=pages, position='top')
pg.run()



