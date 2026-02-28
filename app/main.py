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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st

from common.bootstrap import initialize_backend
from common.services.supermarkets import get_chain_from_code
from backend.services.async_runner import run_async
from backend.db.crud.items import item_details


initialize_backend()
st.write('hello')
# data = run_async(test_item, item_code='7290000072753')
# st.write(data)

st.write(get_chain_from_code('7290027600007'))

