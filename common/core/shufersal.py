import httpx
import asyncio
from bs4 import BeautifulSoup

from backend.app.core.super_class import SupermarketChain
from backend.app.utilities.url_request import url_request


class Shufersal(SupermarketChain):
    abstract = False
    name = 'שופרסל בע"מ (כולל רשת BE)'
    alias = 'shufersal'
    chain_code = '7290027600007'
    url = 'https://prices.shufersal.co.il/'
    link_type = 'shufersal'

    @classmethod
    def extract_date_from_url(cls, url: str) -> dict:
        """ Extract date from the given URL if present. """
        return {'date': url.split('-')[2].split('.')[0]}

    @classmethod
    def extract_store_code_from_url(cls, url: str) -> dict:
        """ Extract store code from the given URL if present. """
        return {'store_code': url.split('-')[1]}

    @classmethod
    def latest(cls, urls: list[str]) -> dict:
        """ Get the latest file URL from the list based on date. """
        return {'latest': max(urls, key=lambda x: cls.extract_date_from_url(x).get('date', '0'))}

    @classmethod
    async def get_file(cls, store_code: int | str | None = None, file_type: int = 0,
                       client: httpx.AsyncClient | None = None) -> dict:
        """
        This function gets defined file for shufersal supermarket chain.
        file-type: 0 - all, 1-price, 2-pricefull, 3-promo, 4-promofull, 5 - stores
        """
        base = cls.url
        # Get file of selected type for the relevant store
        try:
            # Define URL for file list
            url = f"{base}FileObject/UpdateCategory?catID={file_type}&storeId={store_code}"
            # Get response from the URL
            response = await url_request(url, client=client)
            return response

        except ValueError as e:
            return {'Error': str(e)}

    @classmethod
    def parse_response(cls, response: bytes) -> dict[str, list[str | None]]:
        """ This function parses the HTML response using BeautifulSoup. """
        soup = BeautifulSoup(response, "lxml")
        return {'response': [a.get("href") for a in soup.select("table.webgrid tbody tr td a") if a.get("href")]}

    @classmethod
    async def stores(cls, ) -> dict:
        """ This function gets store list for shufersal supermarket chain. """
        response = await cls.get_file(file_type=5, )
        # Check if response contains 'response' key
        if response.get('response'):
            # Parse the response to extract store links
            parsed = cls.parse_response(response.get('response'))
            # Get the latest store url
            latest = cls.latest(parsed.get('response'))
            return {'stores': latest.get('latest')}
        else:
            return response

    @classmethod
    async def prices(cls, store_code: int | str, ) -> dict:
        """ This function gets latest price and promo files for relevant store for the shufersal supermarket chain. """
        async with asyncio.TaskGroup() as tg:
            tasks = {
                'price': tg.create_task(cls._fetch(store_code, 1)),
                'pricefull': tg.create_task(cls._fetch(store_code, 2)),
                'promo': tg.create_task(cls._fetch(store_code, 3)),
                'promofull': tg.create_task(cls._fetch(store_code, 4)),
            }
        # Return dict with file types and latest url for that type - price, pricefull, promo, promofull
        return {name: cls.latest(cls.parse_response(task.result().get('response')).get('response')).get('latest')
                for name, task in tasks.items()}

    @classmethod
    async def _fetch(cls, store_code: int | str, file_type: int):
        """ Helper function to create client used in get_file function """
        async with httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(15.0),
        ) as client:
            return await cls.get_file(store_code, file_type, client=client)

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """
        This function extracts store data from the stores_data_dict extracted from latest stores url
        and prepares it for database insertion.
        """
        # Step 1: Navigate into the SAP structure
        abap = stores_data_dict.get("asx:abap", {})
        values = abap.get("asx:values", {})

        # Step 2: Extract chain-level info
        chain_code = values.get("CHAINID")
        chain_name = None  # often not included here; store_name entries include chain name

        chain_info = {
            "chain_code": chain_code,
            "chain_name": chain_name
        }

        # Step 3: Extract the list of stores
        stores_block = values.get("STORES", {})
        store_list = stores_block.get("STORE", []) or []

        stores = []

        for s in store_list:
            # Subchain info can be in each store entry
            subchain_code = s.get("SUBCHAINID")
            subchain_name = s.get("SUBCHAINNAME")

            store_dict = await cls.as_store_dict(
                s,
                **chain_info,
                subchain_code=subchain_code,
                subchain_name=subchain_name,
            )
            stores.append(store_dict)

        return {"stores_data_list": stores}

    @classmethod
    async def search_for_item(cls, price_data: dict, search_term: str):
        """ Return dicts that has search term """
        return [d for d in price_data if search_term in d['ItemName']]

    @classmethod
    def promo_blacklist(cls) -> set[str]:
        """ Return list of promo blacklist PromotionId's - General promos that should be ignored """
        return {"4305214", "4327051"}



