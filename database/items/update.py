import asyncio

from common.core.super_class import SupermarketChain
from common.db.crud.stores import get_stores_for_chain
from common.pipeline.fresh_price_promo import fresh_price_data