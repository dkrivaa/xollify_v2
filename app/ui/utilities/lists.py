import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from backend.db.supabase import get_database_url
from ui.utilities.upload import InventoryFileHandler


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
        # st.stop()

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

