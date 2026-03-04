import streamlit as st

from common.core.super_class import SupermarketChain
from common.utilities.supermarkets import get_chain_from_code
from backend.services.async_runner import run_async
from backend.db.crud.stores import stores_for_chain


def chain_selector():
    """ Chain selector dropdown """
    # Get all registered supermarket chains
    chains = SupermarketChain.registry
    # Make dict with chain_code as key and alias as value
    code_to_alias = {c.chain_code: c.alias for c in chains}
    # Sort the chain codes by their alias
    sorted_codes = sorted(code_to_alias.keys(), key=lambda x: code_to_alias[x])

    chain = st.selectbox(
        label=f':material/search: Supermarket Chain',
        options=sorted_codes,  # Use sorted list instead of list(code_to_alias)
        format_func=lambda x: code_to_alias[x].capitalize(),
        index=None,
        placeholder='Select Chain',
        key='chain_selector'
    )

    chain_alias = next(c.alias for c in chains if c.chain_code == chain) if chain else None
    # Return chain_code of selected chain
    return chain, chain_alias


def store_selector(chain_code: str):
    """ Gets stores for chain defined by chain_code """
    # Get chain object matching given chain code
    chain = get_chain_from_code(chain_code)

    @st.cache_data(show_spinner='Getting stores for selected chain...', )
    def chain_stores(chain):
        # Wrapper function to get stores for chain with caching
        return run_async(stores_for_chain, chain=chain)

    # Get stores for chain
    stores = chain_stores(chain)

    # Make selectBox to select store
    store = st.selectbox(
        label=f':material/search: Store',
        placeholder='Select Store',
        options=sorted([s['store_code'] for s in stores], key=lambda x: int(x)),
        format_func=lambda x: f'{x} - {next(s['store_name'] for s in stores if s['store_code'] == x)}',
        index=None,
        key='store_selector'
    )

    store_name = next(s['store_name'] for s in stores if s['store_code'] == store) if store else None

    # Return store_code for selected store
    return store, store_name


def item_selector(price_data: list[dict], label: str = 'Item'):
    """ Widget to select item from price data """
    options = [d['ItemCode'] for d in price_data]

    item = st.selectbox(
        label=f':material/search: {label}',
        placeholder='Select Item',
        options=sorted(options, key=int),
        format_func=lambda x: f"{x} - {next(d.get('ItemName') or d.get('ItemNm') for d in price_data
                                            if d['ItemCode'] == x)}",
        index=None,
        key='item_selector'
    )

    return item


def home_store_selector(stores: list[dict]):
    """ Radio widget to select home store """
    idx = st.radio(label='Select',
                   label_visibility='hidden',
                   options=list(range(len(stores))),
                   format_func=lambda x: f"{stores[x].get('chain_alias')} - "
                                         f"{stores[x].get('store_name')}",
                   index=None
                   )
    # Return the dict at index idx
    if idx:
        return stores[idx]

