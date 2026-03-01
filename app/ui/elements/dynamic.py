import streamlit as st

from common.core.super_class import SupermarketChain


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

    # Return chain_code of selected chain
    return chain

