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
        key='store_selector',
        disabled=not chain_code
    )

    store_name = next(s['store_name'] for s in stores if s['store_code'] == store) if store else None

    # Return store_code for selected store
    return store, store_name


def item_selector(price_data: list[dict], label: str = 'Item', key: str = 'item_selector'):
    """ Widget to select item from price data """
    options = [d['ItemCode'] for d in price_data]

    item = st.selectbox(
        label=f':material/search: {label}',
        placeholder='Select Item',
        options=sorted(options, key=int),
        format_func=lambda x: f"{x} - {next(d.get('ItemName') or d.get('ItemNm') for d in price_data
                                            if d['ItemCode'] == x)}",
        index=None,
        key=key
    )

    return item


def price_element(item: str, item_details: dict, store: dict[str, str], delta: bool = False):
    """ Renders a single price element for the given item """
    st.metric(
        label=f":blue[{store['chain_alias']} - {store['store_name']}]",
        label_visibility='visible',
        value=(f"₪ {item_details.get('ItemPrice', 'N/A')}"),
        delta=f"{item} - {item_details.get('ItemName') or item_details.get('ItemNm')}" if delta else None,
        delta_arrow='off',
        delta_color='yellow'
    )

    st.space()


def promo_element(chain: SupermarketChain, promo: dict):
    """ Renders a single promo element according to reward type"""
    # Dispatcher
    PROMO_RENDERERS = {
        '1': render_quantity_discount,
        '2': render_percentage_discount,
        '3': render_percentage_discount,
        '6': render_quantity_discount,
        '10': render_quantity_discount,
    }
    # Get reward type and corresponding handler
    reward_type = promo.get('RewardType')
    handler = PROMO_RENDERERS.get(reward_type, None)
    # Call handler if exists
    handler(chain, promo)


def render_quantity_discount(chain: SupermarketChain, promo: dict):
    """ Renders a single promo element with reward type 1"""
    st.markdown(f"**{promo.get('PromotionDescription', 'N/A')}**")
    st.metric(
        label="Promotion Price",
        value=f"{promo.get('DiscountedPrice', 'N/A')} NIS",
    )
    st.write(f"- Minimum Quantity: {promo.get('MinQty', 'N/A')}")
    st.write(f"- Maximum Quantity: {promo.get('MaxQty', 'N/A')}")
    st.write(f"- Minimum Purchase: {promo.get('MinPurchaseAmnt', 'N/A')}")
    st.write(f"- Target Customers: {chain.promo_audience(promo)}")
    st.write(f"- Valid Until: {promo.get('PromotionEndDate', 'N/A')}")
    st.divider()


def render_percentage_discount(chain: SupermarketChain, promo: dict):
    """ Renders a single promo element with reward type 2"""
    st.markdown(f"**{promo.get('PromotionDescription', 'N/A')}**")
    st.metric(
        label="Promotion Discount",
        value=f"{int(promo.get('DiscountRate')) / 100}%",
    )
    st.write(f"- Minimum Quantity: {promo.get('MinQty', 'N/A')}")
    st.write(f"- Maximum Quantity: {promo.get('MaxQty', 'N/A')}")
    st.write(f"- Target Customers: {chain.promo_audience(promo)}")
    st.write(f"- Valid Until: {promo.get('PromotionEndDate', 'N/A')}")
    st.divider()


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
    if idx is not None:
        return stores[idx]


def popover_content(stores: list[dict]):
    """ Popover content to get "Home Store" """
    st.subheader(body=':material/home: Select "Home Store"')
    st.markdown(body='The "Home Store" is used to select items for your shopping '
                     'and should represent where you normally shop',)

    idx = st.radio(label='Select',
                   label_visibility='hidden',
                   options=list(range(len(stores))),
                   format_func=lambda x: f"{stores[x].get('chain_alias')} - "
                                         f"{stores[x].get('store_name')}",
                   index=None
                   )

    st.markdown('Press anywhere outside the box to close')

    # Return the dict at index idx
    if idx is not None:
        return stores[idx]


def lang():
    # LANGUAGE ###################
    lang = 'english'
    icon_position = 'left'
    hebrew = st.toggle(label='עברית')
    if hebrew:
        lang = 'hebrew'
        icon_position = 'right'
    return lang, icon_position

