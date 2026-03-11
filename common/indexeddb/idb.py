import itertools
import json
import time
from typing import Any

from streamlit_js_eval import streamlit_js_eval

_key_counter = itertools.count()

# LZ-String CDN loader — inlined once per JS snippet that needs it
_LZ_LOADER = """
  const loadLZString = () => new Promise((res) => {
    if (window.LZString) { res(); return; }
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/lz-string/1.5.0/lz-string.min.js';
    s.onload = res;
    document.head.appendChild(s);
  });
"""

# Shared JS helpers for compress / decompress (inlined into each snippet)
_COMPRESS_FN = """
  const compress = (val) => LZString.compressToUTF16(JSON.stringify(val));
"""

_DECOMPRESS_FN = """
  const decompress = (record) => {
    if (!record) return record;
    if (record._lz) {
      try {
        record.value = JSON.parse(LZString.decompressFromUTF16(record.value));
      } catch(e) {
        console.warn('LZ decompress failed for', record.id, e);
      }
      delete record._lz;
    }
    return record;
  };
"""


class IndexedDB:
    """
    A Streamlit-friendly wrapper around browser IndexedDB via streamlit_js_eval.
    Values are transparently compressed with LZ-String (compressToUTF16) to
    reduce WebSocket payload size — especially important for large (>10 MB) datasets
    on mobile / unstable connections.

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

    def put(self, item_id: str, value: Any) -> bool:
        raw = json.dumps({"id": item_id, "value": value})
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {_LZ_LOADER}
            loadLZString().then(() => {{
              {_COMPRESS_FN}
              {self._open_db()}
              req.onsuccess = (e) => {{
                const db = e.target.result;
                const raw = {raw};
                const record = {{
                  id: raw.id,
                  value: compress(raw.value),
                  _lz: true,
                  updated_at: new Date().toISOString()
                }};
                const tx = db.transaction({store_name}, "readwrite");
                tx.objectStore({store_name}).put(record);
                tx.oncomplete = () => resolve(true);
                tx.onerror    = (err) => reject(err);
              }};
              req.onerror = (e) => reject(e.target.error);
            }});
          }})
        """
        return self._eval(js, "put") is True

    def put_many(self, items: list[tuple[str, Any]]) -> bool:
        records = json.dumps([
            {"id": item_id, "value": value}
            for item_id, value in items
        ])
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {_LZ_LOADER}
            loadLZString().then(() => {{
              {_COMPRESS_FN}
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
                    value: compress(item.value),
                    _lz: true,
                    updated_at: now
                  }});
                }});
                tx.oncomplete = () => resolve(true);
                tx.onerror    = (err) => reject(err);
              }};
              req.onerror = (e) => reject(e.target.error);
            }});
          }})
        """
        return self._eval(js, "put_many") is True

    def get(self, item_id: str) -> dict | None:
        store_name = json.dumps(self.store_name)
        item_id_js = json.dumps(item_id)
        js = f"""
          new Promise((resolve, reject) => {{
            {_LZ_LOADER}
            loadLZString().then(() => {{
              {_DECOMPRESS_FN}
              {self._open_db()}
              req.onsuccess = (e) => {{
                const tx = e.target.result.transaction({store_name}, "readonly");
                const getReq = tx.objectStore({store_name}).get({item_id_js});
                getReq.onsuccess = () => resolve(decompress(getReq.result ?? null));
                getReq.onerror   = (err) => reject(err);
              }};
              req.onerror = (e) => reject(e.target.error);
            }});
          }})
        """
        return self._eval(js, "get")

    def get_all(self) -> list[dict]:
        store_name = json.dumps(self.store_name)
        js = f"""
          new Promise((resolve, reject) => {{
            {_LZ_LOADER}
            loadLZString().then(() => {{
              {_DECOMPRESS_FN}
              {self._open_db()}
              req.onsuccess = (e) => {{
                const tx = e.target.result.transaction({store_name}, "readonly");
                const all = tx.objectStore({store_name}).getAll();
                all.onsuccess = () => resolve(all.result.map(decompress));
                all.onerror   = (err) => reject(err);
              }};
              req.onerror = (e) => reject(e.target.error);
            }});
          }})
        """
        return self._eval(js, "get_all") or []

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



# from typing import Any
# import json
# import time
# import itertools
# from streamlit_js_eval import streamlit_js_eval
#
# _key_counter = itertools.count()
#
#
# class IndexedDB:
#     """
#     A Streamlit-friendly wrapper around browser IndexedDB via streamlit_js_eval.
#
#     Usage:
#         db = IndexedDB("MyDatabase", "my_store")
#         db.put("user_1", {"name": "Alice", "age": 30})
#         record = db.get("user_1")
#         all_records = db.get_all()
#         db.delete("user_1")
#         db.clear()
#     """
#
#     def __init__(self, db_name: str = "XollifyDB", store_name: str = "data"):
#         self.db_name = db_name
#         self.store_name = store_name
#
#     def _next_key(self, label: str) -> str:
#         return f"_idb_{label}_{time.time_ns()}_{next(_key_counter)}"
#
#     def _eval(self, js: str, label: str):
#         return streamlit_js_eval(
#             js_expressions=js,
#             want_output=True,
#             key=self._next_key(label),
#         )
#
#     def init(self) -> None:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onupgradeneeded = (e) => {{
#               if (!e.target.result.objectStoreNames.contains({json.dumps(self.store_name)}))
#                 e.target.result.createObjectStore({json.dumps(self.store_name)}, {{ keyPath: "id" }});
#             }};
#             req.onsuccess = () => resolve(true);
#             req.onerror   = (e) => reject(e.target.error);
#           }})
#         """
#         self._eval(js, "init")
#
#     def put(self, item_id: str, value: Any) -> bool:
#         record = json.dumps({"id": item_id, "value": value})
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onupgradeneeded = (e) => {{
#               if (!e.target.result.objectStoreNames.contains({json.dumps(self.store_name)}))
#                 e.target.result.createObjectStore({json.dumps(self.store_name)}, {{ keyPath: "id" }});
#             }};
#             req.onsuccess = (e) => {{
#               const db = e.target.result;
#               const record = {record};
#               record.updated_at = new Date().toISOString();
#               const tx = db.transaction({json.dumps(self.store_name)}, "readwrite");
#               tx.objectStore({json.dumps(self.store_name)}).put(record);
#               tx.oncomplete = () => resolve(true);
#               tx.onerror    = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "put") is True
#
#     def put_many(self, items: list[tuple[str, Any]]) -> bool:
#         records = json.dumps([
#             {"id": item_id, "value": value}
#             for item_id, value in items
#         ])
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onupgradeneeded = (e) => {{
#               if (!e.target.result.objectStoreNames.contains({json.dumps(self.store_name)}))
#                 e.target.result.createObjectStore({json.dumps(self.store_name)}, {{ keyPath: "id" }});
#             }};
#             req.onsuccess = (e) => {{
#               const db = e.target.result;
#               const records = {records};
#               const tx = db.transaction({json.dumps(self.store_name)}, "readwrite");
#               const store = tx.objectStore({json.dumps(self.store_name)});
#               records.forEach(record => {{
#                 record.updated_at = new Date().toISOString();
#                 store.put(record);
#               }});
#               tx.oncomplete = () => resolve(true);
#               tx.onerror    = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "put_many") is True
#
#     def get(self, item_id: str) -> dict | None:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onsuccess = (e) => {{
#               const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
#               const get = tx.objectStore({json.dumps(self.store_name)}).get({json.dumps(item_id)});
#               get.onsuccess = () => resolve(get.result ?? null);
#               get.onerror   = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "get")
#
#     def get_all(self) -> list[dict]:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onsuccess = (e) => {{
#               const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
#               const all = tx.objectStore({json.dumps(self.store_name)}).getAll();
#               all.onsuccess = () => resolve(all.result);
#               all.onerror   = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "get_all") or []
#
#     def delete(self, item_id: str) -> bool:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onsuccess = (e) => {{
#               const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readwrite");
#               tx.objectStore({json.dumps(self.store_name)}).delete({json.dumps(item_id)});
#               tx.oncomplete = () => resolve(true);
#               tx.onerror    = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "delete") is True
#
#     def clear(self) -> bool:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onsuccess = (e) => {{
#               const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readwrite");
#               tx.objectStore({json.dumps(self.store_name)}).clear();
#               tx.oncomplete = () => resolve(true);
#               tx.onerror    = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "clear") is True
#
#     def exists(self, item_id: str) -> bool:
#         return self.get(item_id) is not None
#
#     def count(self) -> int:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onsuccess = (e) => {{
#               const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
#               const cnt = tx.objectStore({json.dumps(self.store_name)}).count();
#               cnt.onsuccess = () => resolve(cnt.result);
#               cnt.onerror   = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "count") or 0
#
#     def get_all_keys(self) -> list[str]:
#         js = f"""
#           new Promise((resolve, reject) => {{
#             const req = indexedDB.open({json.dumps(self.db_name)}, 1);
#             req.onsuccess = (e) => {{
#               const tx = e.target.result.transaction({json.dumps(self.store_name)}, "readonly");
#               const keys = tx.objectStore({json.dumps(self.store_name)}).getAllKeys();
#               keys.onsuccess = () => resolve(keys.result);
#               keys.onerror   = (err) => reject(err);
#             }};
#             req.onerror = (e) => reject(e.target.error);
#           }})
#         """
#         return self._eval(js, "get_all_keys") or []

