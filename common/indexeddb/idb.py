import json
import time
from streamlit_js_eval import streamlit_js_eval
import time
import itertools

_key_counter = itertools.count()


class IndexedDB:
    """
    A Streamlit-friendly wrapper around browser IndexedDB via streamlit_js_eval.

    Usage:
        db = IndexedDB("MyDatabase", "my_store")
        db.put("user_1", {"name": "Alice", "age": 30})
        record = db.get("user_1")
        all_records = db.get_all()
        db.delete("user_1")
        db.clear()
    """

    def __init__(self, db_name: str = "XollifyDB", store_name: str = "data"):
        self.db_name = db_name
        self.store_name = store_name

    # ── Private helpers ────────────────────────────────────────────────────

    def _next_key(self, label: str) -> str:
        """Return a unique streamlit_js_eval key using nanosecond timestamp.
        Survives session resets, page refreshes, and mobile lock/unlock cycles."""
        return f"_idb_{label}_{time.time_ns()}_{next(_key_counter)}"

    def _eval(self, js: str, label: str):
        """Run JS and return the result, using a unique key every call."""
        return streamlit_js_eval(
            js_expressions=js,
            want_output=True,
            key=self._next_key(label),
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def init(self) -> None:
        """
        Pre-create the DB and object store in the browser.
        Optional — the DB is created automatically on first use if not called.
        """
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onupgradeneeded = (e) => {{
              if (!e.target.result.objectStoreNames.contains({json.dumps(self.store_name)}))
                e.target.result.createObjectStore({json.dumps(self.store_name)}, {{ keyPath: "id" }});
            }};
            req.onsuccess = () => resolve(true);
            req.onerror   = (e) => reject(e.target.error);
          }})
        """
        self._eval(js, "init")

    def put(self, item_id: str, value: list | dict | str | int | float) -> bool:
        """
        Insert or update a record. Returns True on success.
        The stored object will be: { id: item_id, value: value, updated_at: <iso> }
        """
        record = json.dumps({"id": item_id, "value": value})
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onupgradeneeded = (e) => {{
              if (!e.target.result.objectStoreNames.contains({json.dumps(self.store_name)}))
                e.target.result.createObjectStore({json.dumps(self.store_name)}, {{ keyPath: "id" }});
            }};
            req.onsuccess = (e) => {{
              const db = e.target.result;
              const record = {record};
              record.updated_at = new Date().toISOString();
              const tx = db.transaction({json.dumps(self.store_name)}, "readwrite");
              tx.objectStore({json.dumps(self.store_name)}).put(record);
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "put") is True

    def get(self, item_id: str) -> dict | None:
        """Fetch a single record by ID. Returns the record dict or None."""
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
              const get = tx.objectStore({json.dumps(self.store_name)}).get({json.dumps(item_id)});
              get.onsuccess = () => resolve(get.result ?? null);
              get.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "get")

    def get_all(self) -> list[dict]:
        """Return all records in the store as a list."""
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
              const all = tx.objectStore({json.dumps(self.store_name)}).getAll();
              all.onsuccess = () => resolve(all.result);
              all.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "get_all") or []

    def delete(self, item_id: str) -> bool:
        """Delete a record by ID. Returns True on success."""
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readwrite");
              tx.objectStore({json.dumps(self.store_name)}).delete({json.dumps(item_id)});
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "delete") is True

    def clear(self) -> bool:
        """Delete all records in the store. Returns True on success."""
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readwrite");
              tx.objectStore({json.dumps(self.store_name)}).clear();
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "clear") is True

    def exists(self, item_id: str) -> bool:
        """Return True if a record with the given ID exists."""
        return self.get(item_id) is not None

    def count(self) -> int:
        """Return the number of records in the store."""
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
              const cnt = tx.objectStore({json.dumps(self.store_name)}).count();
              cnt.onsuccess = () => resolve(cnt.result);
              cnt.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "count") or 0

    def get_all_keys(self) -> list[str]:
        """Return all keys (IDs) in the store."""
        js = f"""
          new Promise((resolve, reject) => {{
            const req = indexedDB.open({json.dumps(self.db_name)}, 1);
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
              const keys = tx.objectStore({json.dumps(self.store_name)}).getAllKeys();
              keys.onsuccess = () => resolve(keys.result);
              keys.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "get_all_keys") or []