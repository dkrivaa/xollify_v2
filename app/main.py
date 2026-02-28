# For streamlit cloud
import subprocess
subprocess.run(["playwright", "install", "chromium"], check=True)

# For streamlit on local
import sys
import asyncio
# Fix for Windows + Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st

from backend.services.async_runner import run_async
from backend.db.crud.items import test_item



st.write('hello')
data = run_async(test_item, '7290000072753')
st.write(data)

