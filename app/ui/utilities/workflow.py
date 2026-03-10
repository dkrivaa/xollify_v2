import streamlit as st
from enum import Enum, auto

from ui.utilities.general import get_stores_missing_data, store_data_for_selected_stores
from ui.elements.static import no_stores_selected, no_home_store_selected
from ui.elements.dialogs import get_home_store


class WorkflowStep(Enum):
    """ Class of workflow steps that need to be met """
    NO_STORES = auto()            # No stores selected
    NO_HOME_STORE = auto()        # Stores selected but no home store
    NO_DATA = auto()              # Stores and home store but data for stores not loaded
    READY = auto()                # All checks passed


def get_workflow_state() -> WorkflowStep:
    """ Get the state of the workflow checks """
    # Check if stores
    stores_record = st.session_state.db.get(item_id='stores')
    stores = (stores_record or {}).get('value', [])
    if not stores:
        return WorkflowStep.NO_STORES

    # Check if home store
    if not st.session_state.db.get(item_id='home_store'):
        return WorkflowStep.NO_HOME_STORE

    # Check if price and promo data for selected stores
    stores_to_fetch = get_stores_missing_data(stores=stores)
    if stores_to_fetch:
        return WorkflowStep.NO_DATA

    return WorkflowStep.READY


def enforce_workflow(required: WorkflowStep = WorkflowStep.READY) -> bool:
    """
    Function that checks if required workflow state is met (returns True, False otherwise).
    Handles the appropriate action to correct state that is not met.
    Param:
        required -

    Any page or section — one line replaces all guards
        enforce_workflow()
    if a page only needs stores but not home store yet:
        enforce_workflow(required=WorkflowStep.NO_HOME_STORE)
    """
    state = get_workflow_state()

    # Handling no stores
    if required.value >= WorkflowStep.NO_STORES.value:
        if state == WorkflowStep.NO_STORES:
            no_stores_selected()
            st.stop()

    # Handling home store
    if required.value >= WorkflowStep.NO_HOME_STORE.value:
        if state == WorkflowStep.NO_HOME_STORE:
            if 'home_store' in st.session_state:
                st.session_state.db.put(item_id='home_store', value=st.session_state['home_store'])
                st.stop()
            elif len(st.session_state.db.get(item_id='stores').get('value')) == 1:
                stores = st.session_state.db.get(item_id='stores').get('value')
                st.session_state.db.put(item_id='home_store', value=stores)
                st.stop()
            else:
                no_home_store_selected()
                st.stop()
            # # If only one store -> set as home_store, else show dialog
            # stores = st.session_state.db.get(item_id='stores').get('value', [])
            # if len(stores) == 1:
            #     st.session_state.db.put(item_id='home_store', value=stores[0])
            #     st.rerun()
            # else:
            #     # Show dialog
            #     get_home_store(stores)
            #     st.stop()

    # Handling no price and promo data for stores
    if required.value >= WorkflowStep.NO_DATA.value:
        if state == WorkflowStep.NO_DATA:
            stores = st.session_state.db.get(item_id='stores').get('value', [])
            store_data_for_selected_stores(stores)
            # st.rerun()

    return True

