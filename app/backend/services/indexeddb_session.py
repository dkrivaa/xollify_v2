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
        record = db.get("user_1")
        db.put_many([("user_1", {"name": "Alice"}), ("user_2", {"name": "Bob"})])
        db.delete("user_1")
        db.clear()
    """

    def __init__(self, db_name: str = "XollifyDB", store_name: str = "data"):
        self._idb = IndexedDB(db_name, store_name)
        self._cache_key = f"_idb_cache_{db_name}_{store_name}"
        if self._cache_key not in st.session_state:
            st.session_state[self._cache_key] = {}

    @property
    def _cache(self) -> dict:
        return st.session_state[self._cache_key]

    def _cache_set(self, item_id: str, record: dict) -> None:
        st.session_state[self._cache_key][item_id] = record

    def _cache_delete(self, item_id: str) -> None:
        st.session_state[self._cache_key].pop(item_id, None)

    def _cache_clear(self) -> None:
        st.session_state[self._cache_key] = {}

    def init(self) -> None:
        self._idb.init()

    def put(self, item_id: str, value: Any) -> bool:
        self._cache_set(item_id, {"id": item_id, "value": value})
        return self._idb.put(item_id, value)

    def put_many(self, items: list[tuple[str, Any]]) -> bool:
        for item_id, value in items:
            self._cache_set(item_id, {"id": item_id, "value": value})
        return self._idb.put_many(items)

    def get(self, item_id: str, default: Any = None) -> dict | Any:
        if item_id in self._cache:
            return self._cache[item_id]
        if st.session_state.get("db_ready"):
            return default  # cache is authoritative after startup
        record = self._idb.get(item_id)
        if record is not None:
            self._cache_set(item_id, record)
            return record
        return default

    def get_all(self) -> list[dict]:
        if self._cache:
            return list(self._cache.values())
        records = self._idb.get_all()
        for record in records:
            self._cache_set(record["id"], record)
        return records

    def delete(self, item_id: str) -> bool:
        self._cache_delete(item_id)
        return self._idb.delete(item_id)

    def clear(self) -> bool:
        self._cache_clear()
        return self._idb.clear()

    def exists(self, item_id: str) -> bool:
        if item_id in self._cache:
            return True
        return self._idb.exists(item_id)

    def count(self) -> int:
        if self._cache:
            return len(self._cache)
        return self._idb.count()

    def get_all_keys(self) -> list[str]:
        if self._cache:
            return list(self._cache.keys())
        return self._idb.get_all_keys()

    def invalidate(self, item_id: str | None = None) -> None:
        if item_id is None:
            self._cache_clear()
        else:
            self._cache_delete(item_id)

    def recover_if_needed(self) -> bool:
        if not self._cache:
            records = self._idb.get_all()
            if records:
                for record in records:
                    self._cache_set(record["id"], record)
                return True
        return False
