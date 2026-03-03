from typing import Any
import streamlit as st
from common.indexeddb.idb import IndexedDB


class SessionIndexedDB:
    """
    A Streamlit-specific wrapper around IndexedDB that adds a session_state
    buffer layer. Reads are served from session_state when available, falling
    back to IndexedDB and then caching the result. Writes go to both layers
    immediately — the session_state cache is updated synchronously without
    waiting for the async IndexedDB JS round trip to complete.

    Usage:
        db = SessionIndexedDB()
        db.put("user_1", {"name": "Alice"})
        record = db.get("user_1")   # served from session_state instantly
        db.delete("user_1")
        db.clear()
    """

    def __init__(self, db_name: str = "XollifyDB", store_name: str = "data"):
        self._idb = IndexedDB(db_name, store_name)
        self._cache_key = f"_idb_cache_{db_name}_{store_name}"
        if self._cache_key not in st.session_state:
            st.session_state[self._cache_key] = {}

    # ── Private helpers ────────────────────────────────────────────────────

    @property
    def _cache(self) -> dict:
        return st.session_state[self._cache_key]

    def _cache_set(self, item_id: str, record: dict) -> None:
        st.session_state[self._cache_key][item_id] = record

    def _cache_delete(self, item_id: str) -> None:
        st.session_state[self._cache_key].pop(item_id, None)

    def _cache_clear(self) -> None:
        st.session_state[self._cache_key] = {}

    # ── Public API ─────────────────────────────────────────────────────────

    def init(self) -> None:
        """Pre-create the DB and object store in the browser. Optional."""
        self._idb.init()

    def put(self, item_id: str, value: Any) -> bool:
        """
        Insert or update a record.
        Writes to session_state immediately (synchronous), then fires the
        IndexedDB JS call asynchronously. Returns True on success.
        """
        self._cache_set(item_id, {"id": item_id, "value": value})
        return self._idb.put(item_id, value)

    def get(self, item_id: str, default: Any = None) -> dict | Any:
        """
        Fetch a single record by ID.
        Tries session_state first; falls back to IndexedDB and caches the result.
        Returns default if not found anywhere.
        """
        if item_id in self._cache:
            return self._cache[item_id]

        record = self._idb.get(item_id)
        if record is not None:
            self._cache_set(item_id, record)
            return record

        return default

    def get_all(self) -> list[dict]:
        """
        Return all records.
        If the cache is populated, returns from session_state.
        Otherwise fetches from IndexedDB and populates the cache.
        """
        if self._cache:
            return list(self._cache.values())

        records = self._idb.get_all()
        for record in records:
            self._cache_set(record["id"], record)
        return records

    def delete(self, item_id: str) -> bool:
        """Delete a record from both session_state and IndexedDB."""
        self._cache_delete(item_id)
        return self._idb.delete(item_id)

    def clear(self) -> bool:
        """Delete all records from both session_state and IndexedDB."""
        self._cache_clear()
        return self._idb.clear()

    def exists(self, item_id: str) -> bool:
        """Return True if a record exists. Checks session_state first."""
        if item_id in self._cache:
            return True
        return self._idb.exists(item_id)

    def count(self) -> int:
        """
        Return the number of records.
        Uses session_state count if cache is populated, otherwise asks IndexedDB.
        """
        if self._cache:
            return len(self._cache)
        return self._idb.count()

    def get_all_keys(self) -> list[str]:
        """
        Return all keys.
        Uses session_state keys if cache is populated, otherwise asks IndexedDB.
        """
        if self._cache:
            return list(self._cache.keys())
        return self._idb.get_all_keys()

    def invalidate(self, item_id: str | None = None) -> None:
        """
        Manually invalidate the session_state cache.
        Pass an item_id to invalidate a single record, or None to invalidate all.
        Useful if IndexedDB was written to directly or from another tab.
        """
        if item_id is None:
            self._cache_clear()
        else:
            self._cache_delete(item_id)