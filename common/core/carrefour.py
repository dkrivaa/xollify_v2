import httpx
import asyncio
import re
from datetime import datetime
import json

from backend.app.utilities.url_request import url_request
from backend.app.core.super_class import SupermarketChain


class CarrefourParent(SupermarketChain):
    abstract = True

    @classmethod
    async def get_files(cls, client: httpx.AsyncClient | None = None) -> dict:
        """
        This function gets store list for carrefour supermarket chain.
        """
        base = await cls.get_url()
        # Get store list
        try:
            # Get response from the URL
            response = await url_request(base, client=client)
            html = response['response'].decode('utf-8', errors='ignore')

            # Extract JSON - handles both JSON.parse`...` and direct array [...] - in the source file
            match = re.search(r'const\s+files\s*=\s*(?:JSON\.parse`(.*?)`|\s*(\[.*?\]))', html, re.DOTALL)
            if not match:
                return {"Error": "No JSON array found on page"}

            # Get whichever group matched (group 1 for JSON.parse, group 2 for direct array of dicts)
            json_str = match.group(1) or match.group(2)
            try:
                files = json.loads(json_str)
                # If match is of second type => extract value of 'name' key in all the dicts in json
                if json_str == match.group(2):
                    files = [d['name'] for d in files]
                return {"response": files}
            except json.JSONDecodeError as e:
                return {"Error": f"JSON parsing failed: {e}"}

        except httpx.HTTPStatusError as e:
            return {'Error': f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {'Error': f"Request error: {str(e)}"}

    @classmethod
    async def make_date_str(cls) -> str:
        """ This function makes date string in YYYYMMDD format. """
        from datetime import datetime
        today = datetime.today()
        return today.strftime("%Y%m%d")

    @classmethod
    async def full_url(cls, data: list[str]) -> list[str]:
        """ This function constructs full URLs for carrefour files. """
        base = await cls.get_url()
        date = await cls.make_date_str()

        return [f'{base}{date}/{url}' for url in data]

    @classmethod
    async def full_urls(cls, client: httpx.AsyncClient | None = None) -> dict:
        """ This function gets all urls list for carrefour supermarket chain. """
        files_data = await cls.get_files(client=client)
        if 'Error' in files_data:
            return files_data

        files = files_data['response']
        full_urls = await cls.full_url(files)

        return {'full_urls': full_urls}

    @classmethod
    async def latest_stores(cls, urls: list[str]) -> str:
        """ Get the latest store file from a given list of URLs. """
        def extract_date(url: str):
            # Extract the date and time using regex
            match = re.search(r'/(\d{8})/.*-(\d{8})-(\d{6})\.xml$', url)
            if match:
                folder_date, file_date, file_time = match.groups()
                return int(f"{file_date}{file_time}")

        return max(urls, key=lambda url: extract_date(url))

    @classmethod
    async def latest_prices(cls, urls: list[str]) -> str:
        """ Get the latest price/promo file from a given list of URLs. """
        def extract_datetime(url: str):
            # # Extract the date and time
            # return int(url.split('-')[-1].split('.')[0])
            # Pattern matches YYYYMMDD followed by optional HHMM or HHMMSS
            pattern = r'(\d{8})(?:-?(\d{4,6}))?'

            match = re.search(pattern, url)
            if match:
                date_part = match.group(1)  # YYYYMMDD
                time_part = match.group(2)  # HHMM or HHMMSS (if exists)

                if time_part:
                    if len(time_part) == 4:
                        # HHMM format
                        datetime_str = date_part + time_part
                        return datetime.strptime(datetime_str, '%Y%m%d%H%M')
                    elif len(time_part) == 6:
                        # HHMMSS format
                        datetime_str = date_part + time_part
                        return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
                else:
                    # Date only
                    return datetime.strptime(date_part, '%Y%m%d')

            return None
        return max(urls, key=lambda url: extract_datetime(url))

    @classmethod
    async def stores(cls, client: httpx.AsyncClient | None = None) -> dict:
        """ This function gets latest store list for carrefour supermarket chain. """
        all_urls = await cls.full_urls()
        # If no errors:
        if 'Error' not in all_urls.keys():
            store_urls = [url for url in all_urls['full_urls'] if 'store' in url.lower()]
            latest = await cls.latest_stores(store_urls)
            return {'stores': store_urls[0] if store_urls else 'No Url'}
        else:
            return all_urls

    @classmethod
    async def price_urls_by_type(cls, urls: list[str]) -> dict:
        """ This function organizes price and promo URLs by type for selected Carrefour supermarket store. """
        types = ["PromoFull", "Promo", "PriceFull", "Price"]
        urls_by_type_dict = {t: [] for t in types}
        for url in urls:
            for t in types:
                if t in url:
                    urls_by_type_dict[t].append(url)
                    break
        return urls_by_type_dict

    @classmethod
    async def prices(cls, store_code: int | str = None) -> dict:
        """ This function gets price and promo files for selected carrefour supermarket chain. """
        # All urls for the chain
        all_urls = await cls.full_urls()
        # If no errors:
        if 'Error' not in all_urls.keys():
            # Price and promo files for the selected store
            price_urls = [url for url in all_urls['full_urls'] if int(url.split('-')[1]) == int(store_code)]
            # Organize Urls by type and get latest for each type
            price_urls_dict = await cls.price_urls_by_type(price_urls)
            for key in price_urls_dict.keys():
                if price_urls_dict[key]:
                    price_urls_dict[key] = await cls.latest_prices(price_urls_dict[key])
                else:
                    price_urls_dict[key] = None
            return price_urls_dict
        else:
            return all_urls

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """
        This function extracts store data from the stores_data_dict extracted from latest stores url
        and prepares it for database insertion.
        """
        root = stores_data_dict.get("Root", {})
        sub = root.get("SubChains", {}).get("SubChain", {})
        chain_info = {
            "chain_code": root.get("ChainID"),
            "chain_name": root.get("ChainName"),
        }

        stores = []
        for s in sub.get("Stores", {}).get("Store", []):
            stores.append(await cls.as_store_dict(s, **chain_info, subchain_code=sub.get("SubChainId")
                                                  , subchain_name=sub.get("SubChainName")))
        return {'stores_data_list': stores}

    @classmethod
    async def search_for_item(cls, price_data: dict, search_term: str):
        """ Return dicts that has search term """
        return [d for d in price_data if search_term in d['ItemName']]

    @classmethod
    def promo_blacklist(cls) -> set[str]:
        """ Return list of promo blacklist PromotionId's - General promos that should be ignored """
        return {'11366992', '11211378', '11347342'}  # When blacklist the format should be: {"4305214"}


class Carrefour(CarrefourParent):
    abstract = False
    name = 'קרפור/ ביתן אונליין'
    alias = 'carrefour'
    chain_code = '7290055700007'
    url = 'https://prices.carrefour.co.il/'
    link_type = 'carrefour'


# class Quik(CarrefourParent):
#     abstract = False
#     name = 'קוויק'
#     alias = 'quick'
#     chain_code = '7291029710008'
#     url = 'https://prices.quik.co.il/'
#     link_type = 'carrefour'