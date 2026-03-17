import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import copy

from backend.db.crud.items import item_details
from backend.services.async_runner import run_async
from backend.db.supabase import get_database_url
from ui.utilities.upload import InventoryFileHandler
from ui.utilities.items import data_for_store_from_db
from ui.utilities.general import make_store_key
from ui.utilities.items import data_for_store_from_db, get_alternative_item


def read_uploaded_file(uploaded_file: UploadedFile) -> list[dict]:
    """Read uploaded file, validate format and check barcodes against Item DB.

    Returns list of dicts with item_code and quantity for valid items only.
    Not-found and invalid rows are surfaced to the user via Streamlit warnings.
    """
    # Get the supabase database url
    DATABASE_URL = get_database_url()

    handler = InventoryFileHandler(DATABASE_URL)
    detected, result = handler.process(uploaded_file)  # ← was `uploaded`, should be `uploaded_file`

    if not detected.is_valid:
        st.error("Could not detect barcode and quantity columns.")
        st.stop()

    if result.not_found:
        st.warning(f"{len(result.not_found)} barcodes not found in DB:")
        for row in result.not_found:
            st.write(f"- {row['barcode']} (qty: {row['quantity']})")

    if result.invalid_rows:
        st.warning(f"{len(result.invalid_rows)} rows had bad data:")
        for row in result.invalid_rows:
            st.write(f"- Row {row['row']}: {row['error']}")

    items = [
        {"item_code": row.barcode, "quantity": row.quantity}
        for row in result.valid_rows
    ]

    if items:
        st.success(f"{len(items)} items ready.")

    return items


def enrich_items_list_from_store(items_list: list[dict], store: dict) -> list[dict]:
    """ Adding item name and item price to items in uploaded shopping list from given store """
    price_data = data_for_store_from_db(store=store, data_type='price')

    # Build a lookup by ItemCode once
    lookup = {d["ItemCode"]: d for d in price_data}
    # Keys to copy
    keyA = "ItemPrice"
    keyB_options = ("ItemName", "ItemNm")  # any of these may exist
    # Find matching dict in price_data
    for s in items_list:
        match = lookup.get(s["item_code"], {})
        # If item code found in price data
        if match:
            # Add keyA if present
            if keyA in match:
                s['item_price'] = match[keyA]
            # Add item name if present in either version
            for keyB in keyB_options:
                if keyB in match:
                    s["item_name"] = match[keyB]
                    break

    return items_list


def enrich_items_list_from_db(items_list: list[dict]) -> list[dict]:
    """ Adding item name for given item in items list that is not available in store """
    # Get list of items without item name
    relevant_items_to_enrich = [item for item in items_list if not item.get('item_name')]
    # Get item name from db for item
    for item in relevant_items_to_enrich:
        item_db_details = run_async(item_details, item_code=item['item_code'])
        item['item_name'] = item_db_details.get('ItemName')

    # return the enriched list
    return items_list


def shoppinglist_for_store(store: dict):
    """ Make shoppinglist for given store from items list """
    # Get items list
    items_list = st.session_state.db.get(item_id='items_list', default={}).get('value', [])
    items_list = copy.deepcopy(items_list)  # ← work on a independent copy

    # Get price data for store:
    price_data = data_for_store_from_db(store=store, data_type='price')

    for item in items_list:
        item_details = next((d for d in price_data if d['ItemCode'] == item['item_code']), None)

        # Item not in store
        if not item_details:
            # Get alternative data from dialog
            effective_item, quantity, item_dict = get_alternative_item(store=store, item=item['item_code'])
            # Update items_list with dialog data
            item['item_code'] = effective_item
            if quantity is not None and float(quantity) != float(item['quantity']):
                item['quantity'] = quantity
            item['item_name'] = item_dict.get('ItemName') or item_dict.get('ItemNm')
            item['item_price'] = item_dict.get('ItemPrice')

        # Item in store
        else:
            item['item_name'] = item_details.get('ItemName') or item_details.get('ItemNm')
            item['item_price'] = item_details.get('ItemPrice')

    return items_list

    # # Add store shoppinglist to session state and indexedDB
    # item_id = f"{store['chain_code']}_{store['store_code']}_shoppinglist"
    # st.session_state.db.put(item_id=item_id, value=items_list)
    # st.stop()


