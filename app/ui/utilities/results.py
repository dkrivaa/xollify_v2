import streamlit as st
import itertools
import math


def organize_shoppinglists() -> list[dict]:
    """ This function organizes all shoppinglists dicts into list accepted in  best_cost_for_k_stores """
    # Empty list to hold shopping dicts for all stores
    shoppinglists = []

    # Get stores
    stores = st.session_state.db.get(item_id='stores').get('value')
    # Make keys
    store_keys = [f"{s['chain_code']}_{s['store_code']}_shoppinglist" for s in stores]
    # Get dict for each store and append to shoppinglists
    for key in store_keys:
        store_list = {k: v for k, v in st.session_state.db.get(item_id=key).items() if k != 'updated_at'}
        shoppinglists.append(store_list)

    return shoppinglists



# updated version
def best_cost_for_k_stores(shoppinglist: list[dict], k: int):
    """
    Calculate the best cost for shoppinglist using k stores.

    Args:
        shoppinglist: list of dicts like:
            [{"id": "chain_store_shoppinglist", "value": [{"item_code": ..., "quantity": ..., "item_name": ..., "item_price": ...}, ...]}, ...]
        k: max number of stores to visit

    Returns:
        best_combo: tuple of store keys with lowest total cost
        best_total: total cost for best combination
        best_plan: dict of {store: [items assigned to that store]}
    """
    # Build internal format: {store_id: [items]}
    # Use id (stripped of '_shoppinglist') as store key
    store_items = {
        entry['id'].removesuffix('_shoppinglist'): entry['value']
        for entry in shoppinglist
    }

    stores = list(store_items.keys())

    # All store lists must have same items in same order - keyed by item_code
    # Build unified item index from first store
    item_codes = [item['item_code'] for item in next(iter(store_items.values()))]
    n_items = len(item_codes)

    # ---- Build price maps: {store: {item_index: float(price)}} ----
    price_maps = {
        store: {i: float(store_items[store][i]['item_price']) for i in range(n_items)}
        for store in stores
    }

    best_combo = None
    best_total = math.inf
    best_plan = None

    # ---- Try all store combinations up to size k ----
    for r in range(1, k + 1):
        for combo in itertools.combinations(stores, r):

            store_plan = {s: [] for s in combo}
            total_cost = 0

            for i in range(n_items):
                available = [(store, price_maps[store][i]) for store in combo]
                best_store, unit_price = min(available, key=lambda x: x[1])

                qty = float(store_items[best_store][i]['quantity'])
                cost = unit_price * qty

                store_plan[best_store].append({
                    'item': item_codes[i],
                    'item_name': store_items[best_store][i]['item_name'],
                    'quantity': qty,
                    'unit_price': unit_price,
                    'total_price': cost
                })

                total_cost += cost

            if total_cost < best_total:
                best_total = total_cost
                best_combo = combo
                best_plan = store_plan

    return best_combo, best_total, best_plan


# Original version from Xollify (v1)
# def best_cost_for_k_stores(shoppinglist, k):
#     """
#     Calculate the best cost for shoppinglist using k stores.
#
#     Tries all combinations of up to k stores and finds the combination
#     where buying each item at the cheapest available store yields the lowest total cost.
#
#     Args:
#         shoppinglist: {
#             "StoreA": [ {"Item Code": ..., "Product Name": ..., "Quantity": ..., "price": ...}, ... ],
#             "StoreB": [...],
#             ...
#         }
#         k: max number of stores to visit
#
#     Returns:
#         best_combo: tuple of store keys with lowest total cost
#         best_total: total cost for best combination
#         best_plan: dict of {store: [items assigned to that store]}
#     """
#     stores = list(shoppinglist.keys())
#
#     # Number of items (all store lists are the same length)
#     n_items = len(next(iter(shoppinglist.values())))
#
#     # ---- Build price maps: {store: {item_index: float(price)}} ----
#     price_maps = {
#         store: {i: float(shoppinglist[store][i]["price"]) for i in range(n_items)}
#         for store in stores
#     }
#
#     best_combo = None
#     best_total = math.inf
#     best_plan = None
#
#     # ---- Try all store combinations up to size k ----
#     for r in range(1, k + 1):
#         for combo in itertools.combinations(stores, r):
#
#             store_plan = {s: [] for s in combo}
#             total_cost = 0
#
#             for i in range(n_items):
#                 # Get available prices for this item across stores in combo
#                 available = [(store, price_maps[store][i]) for store in combo]
#
#                 # Choose the cheapest store for this item
#                 best_store, unit_price = min(available, key=lambda x: x[1])
#
#                 # Take quantity from the assigned store
#                 qty = shoppinglist[best_store][i]["Quantity"]
#                 cost = unit_price * qty
#
#                 store_plan[best_store].append({
#                     'item': shoppinglist[best_store][i]["Item Code"],
#                     'item_name': shoppinglist[best_store][i]["Product Name"],  # name from assigned store
#                     'quantity': qty,
#                     'unit_price': unit_price,
#                     'total_price': cost
#                 })
#
#                 total_cost += cost
#
#             # Record best result if this combo is cheaper
#             if total_cost < best_total:
#                 best_total = total_cost
#                 best_combo = combo
#                 best_plan = store_plan
#
#     return best_combo, best_total, best_plan

