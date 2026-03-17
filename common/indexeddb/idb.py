import base64
import itertools
import json
import time
import zlib
from typing import Any

from streamlit_js_eval import streamlit_js_eval

_key_counter = itertools.count()


def _compress(value: Any) -> str:
    """Compress a Python value to a base64-encoded zlib string."""
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    return base64.b64encode(zlib.compress(raw, level=9)).decode("utf-8")


def _decompress(value: str) -> Any:
    """Decompress a base64-encoded zlib string back to a Python value."""
    raw = zlib.decompress(base64.b64decode(value.encode("utf-8")))
    return json.loads(raw.decode("utf-8"))


class IndexedDB:
    """
    A Streamlit-friendly wrapper around browser IndexedDB via streamlit_js_eval.
    Values are compressed with zlib in Python before sending over WebSocket,
    and decompressed in Python after receiving — keeping JS simple and reducing
    WebSocket payload size significantly for large datasets on mobile / unstable connections.

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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_key(self, label: str) -> str:
        return f"_idb_{label}_{time.time_ns()}_{next(_key_counter)}"

    def _eval(self, js: str, label: str):
        return streamlit_js_eval(
            js_expressions=js,
            want_output=True,
            key=self._next_key(label),
        )

    def _open_db(self) -> str:
        """Returns JS snippet that opens the DB (reused in every method)."""
        db_name = json.dumps(self.db_name)
        store_name = json.dumps(self.store_name)
        return f"""
          const req = indexedDB.open({db_name}, 1);
          req.onupgradeneeded = (e) => {{
            if (!e.target.result.objectStoreNames.contains({store_name}))
              e.target.result.createObjectStore({store_name}, {{ keyPath: "id" }});
          }};
        """

    def _decompress_record(self, record: dict | None) -> dict | None:
        """Decompress a record's value if it was compressed with zlib."""
        if record and record.get("_zlib"):
            record["value"] = _decompress(record["value"])
        return record

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init(self) -> None:
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = () => resolve(true);
            req.onerror   = (e) => reject(e.target.error);
          }})
        """
        self._eval(js, "init")

    def put(self, item_id: str, value: Any) -> bool | None:
        compressed = _compress(value)
        record = json.dumps({"id": item_id, "value": compressed, "_zlib": True})
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const db = e.target.result;
              const record = {record};
              record.updated_at = new Date().toISOString();
              const tx = db.transaction({store_name}, "readwrite");
              tx.objectStore({store_name}).put(record);
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        result = self._eval(js, "put")
        if result is None:
            return None
        return result is True

    def put_many(self, items: list[tuple[str, Any]]) -> bool | None:
        records = json.dumps([
            {"id": item_id, "value": _compress(value), "_zlib": True}
            for item_id, value in items
        ])
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const db = e.target.result;
              const items = {records};
              const tx = db.transaction({store_name}, "readwrite");
              const store = tx.objectStore({store_name});
              const now = new Date().toISOString();
              items.forEach(item => {{
                store.put({{
                  id: item.id,
                  value: item.value,
                  _zlib: true,
                  updated_at: now
                }});
              }});
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        result = self._eval(js, "put_many")
        if result is None:
            return None
        return result is True

    def get(self, item_id: str) -> dict | None:
        store_name = json.dumps(self.store_name)
        item_id_js = json.dumps(item_id)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({store_name}, "readonly");
              const getReq = tx.objectStore({store_name}).get({item_id_js});
              getReq.onsuccess = () => resolve(getReq.result ?? null);
              getReq.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        record = self._eval(js, "get")
        return self._decompress_record(record)

    def get_all(self) -> list[dict] | None:
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({store_name}, "readonly");
              const all = tx.objectStore({store_name}).getAll();
              all.onsuccess = () => resolve(all.result);
              all.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        records = self._eval(js, "get_all")
        if records is None:
            return None
        return [self._decompress_record(r) for r in records]

    def delete(self, item_id: str) -> bool:
        store_name = json.dumps(self.store_name)
        item_id_js = json.dumps(item_id)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({store_name}, "readwrite");
              tx.objectStore({store_name}).delete({item_id_js});
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "delete") is True

    def clear(self) -> bool:
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({store_name}, "readwrite");
              tx.objectStore({store_name}).clear();
              tx.oncomplete = () => resolve(true);
              tx.onerror    = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "clear") is True

    def exists(self, item_id: str) -> bool:
        return self.get(item_id) is not None

    def count(self) -> int:
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({store_name}, "readonly");
              const cnt = tx.objectStore({store_name}).count();
              cnt.onsuccess = () => resolve(cnt.result);
              cnt.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "count") or 0

    def get_all_keys(self) -> list[str]:
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {self._open_db()}
            req.onsuccess = (e) => {{
              const tx = e.target.result.transaction({store_name}, "readonly");
              const keys = tx.objectStore({store_name}).getAllKeys();
              keys.onsuccess = () => resolve(keys.result);
              keys.onerror   = (err) => reject(err);
            }};
            req.onerror = (e) => reject(e.target.error);
          }})
        """
        return self._eval(js, "get_all_keys") or []