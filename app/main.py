
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
import json


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
import time
from backend.services.indexeddb_session import SessionIndexedDB

# Retry and timeout defaults for restoration from indexedDB (after mobile lock)
_IDB_MAX_RETRIES = 3
_IDB_TIMEOUT_SECS = 8

if "db" not in st.session_state:
    st.session_state.db = SessionIndexedDB(f"XollifyDB_{sid}", "data")
    st.session_state.db.init()
    st.session_state.db_ready = False
    st.session_state._idb_state = "pending"
    st.session_state._idb_attempts = 0
    st.session_state._idb_started_at = None

    # Delete all orphaned XollifyDB_* databases that don't match current sid
    current_db = f"XollifyDB_{sid}"
    st.session_state.db._idb._eval(f"""
          new Promise(async (resolve) => {{
            const databases = await indexedDB.databases();
            for (const db of databases) {{
              if (db.name.startsWith('XollifyDB_') && db.name !== {json.dumps(current_db)}) {{
                indexedDB.deleteDatabase(db.name);
              }}
            }}
            resolve(true);
          }})
    """, "cleanup_orphans")

if not st.session_state.db_ready:
    state = st.session_state._idb_state

    if state == "pending":
        # Fire JS request and start timer
        st.session_state._idb_started_at = time.time()
        st.session_state.db._idb.get_all()
        st.session_state._idb_state = "loading"
        st.stop()

    elif state == "loading":
        records = st.session_state.db._idb.get_all()
        elapsed = time.time() - st.session_state._idb_started_at

        if records is None:
            # JS still pending — check for timeout
            if elapsed > _IDB_TIMEOUT_SECS:
                attempts = st.session_state._idb_attempts + 1
                st.session_state._idb_attempts = attempts
                if attempts >= _IDB_MAX_RETRIES:
                    st.session_state._idb_state = "failed"
                else:
                    # Retry: re-fire JS request
                    st.session_state._idb_started_at = time.time()
            st.stop()

        elif records:
            for record in records:
                st.session_state.db._cache_set(record["id"], record)
            st.session_state._idb_state = "done"
            st.session_state.db_ready = True

        else:
            # JS resolved with [] — new session, nothing to restore
            st.session_state._idb_state = "done"
            st.session_state.db_ready = True

    elif state == "failed":
        # All retries exhausted — proceed without restored data
        st.warning("Session could not be restored. Some data may be missing.")
        st.session_state.db_ready = True

# Post-lock recovery: cache empty but db_ready=True and get_all data exists
elif not st.session_state.db._cache:
    for key, val in st.session_state.items():
        if key.startswith("_idb_get_all_") and isinstance(val, list) and val:
            for record in val:
                if record.get("id"):
                    st.session_state.db._cache_set(record["id"], record)
            break

# LANGUAGE ###################



# PAGE DEFINITIONS ###########
pages = {
    'home_page_old': st.Page(
        title='Xollify_old',
        page='ui/views/home_old.py',
        icon=':material/home:',
        default=True,
    ),
    'home_page': st.Page(
        title='Xollify-Home',
        page='ui/views/home_view.py',
        icon=':material/home:',
    ),
    'home_store_page': st.Page(
        title='Xollify-Home Store',
        page='ui/views/home_store_view.py',
        icon=':material/storefront:',
    ),
    'other_stores_page': st.Page(
        title='Xollify-Stores',
        page='ui/views/other_stores_view.py',
        icon=':material/storefront:',
    ),
    'selected_stores_page': st.Page(
        title='Xollify-Selected Stores',
        page='ui/views/selected_stores_view.py',
        icon=':material/storefront:',
    ),
    'items_page': st.Page(
        title='Xollify-Product Price',
        page='ui/views/items_view.py',
        icon=':material/shopping_cart:',
    ),
    'lists_page': st.Page(
        title='Xollify-Shopping List',
        page='ui/views/lists_view.py',
        icon=':material/list:',
    ),
    'results_page': st.Page(
        title='Xollify-results',
        page='ui/views/results_view.py',
        icon=':material/brand_awareness:',
    ),
}

preconditions = {
    # 'selected_stores_page': lambda: 'stores' in st.session_state.db.get_all_keys(),
    "analysis": lambda: (
        st.session_state.db.exists("some_price_key") and
        st.session_state.get("filters_set")
    ),
}
# Or if the conditions get complex, a named function is cleaner:
# def analysis_ready() -> bool:
#     return (
#         st.session_state.db.exists("some_price_key") and
#         st.session_state.get("filters_set") and
#         st.session_state.get("some_other_condition")
#     )

# preconditions = {
#     "filter":   lambda: st.session_state.db.exists("some_price_key"),
#     "analysis": analysis_ready,
# }

accessible = set()
if st.session_state.get("db_ready"):
    accessible = {
        name for name in pages
        if name not in preconditions or preconditions[name]()
    }

# st.navigation gets a list of st.Page objects, filtered by accessibility
nav_pages = [pages[name] for name in accessible]
pg = st.navigation(nav_pages, position="top")
pg.run()


# home_page = st.Page(
#     title='Xollify',
#     page='ui/views/home_old.py',
#     icon=':material/home:',
#     default=True,
# )
#
# pages = [home_page]
#
# # RUN APP ###########
# pg = st.navigation(pages=pages, position='top')
# pg.run()
#


