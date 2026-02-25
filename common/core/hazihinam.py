import httpx
from bs4 import BeautifulSoup
import asyncio
import re

from backend.app.utilities.url_request import url_request
from backend.app.core.super_class import SupermarketChain


class HaziHinam(SupermarketChain):
    abstract = False
    name = 'כל בו חצי חינם בע"מ'
    alias = 'hazihinam'
    chain_code = '7290700100008'
    url = 'https://shop.hazi-hinam.co.il/Prices'
    link_type = 'hazihinam'


    @classmethod
    async def get_num_pages(cls, html: str) -> dict:
        """
        This function gets the number of pages for HaziHinam supermarket chain.
        """
        soup = BeautifulSoup(html, "lxml")
        pagination = soup.find("ul", class_="pagination")
        li_items = pagination.find_all("li")
        if not pagination:
            li_items = 0
        return {'response': len(li_items)}

    @classmethod
    async def parse_html_for_files(cls, html: str) -> dict:
        """ Parse HTML to extract file URLs. """
        soup = BeautifulSoup(html, "lxml")
        links = [
            a["href"]
            for a in soup.find_all("a", href=True)
            if a["href"].startswith("https://hazihinamprod01.blob.core.windows.net/regulatories/")
        ]
        return {'result': links}

    @classmethod
    async def get_files(cls, file_type: int = None, client: httpx.AsyncClient | None = None) -> dict:
        """
        This function gets all urls of given file type for HaziHinam supermarket chain.
        """
        base = await cls.get_url()
        # Request the first page to determine total number of pages
        response = await url_request(f'{base}?t={file_type}', client=client)
        html = response.get('response', '')
        pages = await cls.get_num_pages(html)
        page_num = pages.get('response', 0)

        urls = []
        # Urls for first page
        extracted_urls = await cls.parse_html_for_files(html)
        urls.extend(extracted_urls.get('result', []))

        # Loop through all pages to get URLs
        try:
            responses = []
            tasks = [url_request(f'{base}?p={page}&t={file_type}', client=client)
                     for page in range(2, page_num + 1)]
            responses += await asyncio.gather(*tasks)
            for resp in responses:
                links = await cls.parse_html_for_files(resp.get('response', ''))
                urls.extend(links.get('result', []))

            return {'response': urls}

        except Exception as e:
            return {'Error': str(e)}

    @classmethod
    async def latest(cls, urls: list[str]) -> str:
        """ Get the latest file from a given list of URLs. """
        def extract_date(url: str):
            match = re.search(r"(\d{8})-(\d{6})", url)
            if match:
                date_str, time_str = match.groups()  # '20251108', '100919'
                combined_int = int(date_str + time_str)  # → 20251108100919
                return combined_int

        return max(urls, key=lambda url: extract_date(url))

    @classmethod
    async def stores(cls, file_type: int = 3, client: httpx.AsyncClient | None = None):
        """ This function gets store list for hazihinam supermarket chain. """
        try:
            # Get all file links
            file_links = await cls.get_files(file_type=file_type, client=client)
            all_urls = file_links.get('response', [])
            # Get the latest store file
            latest_store = await cls.latest(all_urls) if all_urls else None
            return {'stores': latest_store}
        except Exception as e:
            return {'Error': str(e)}

    @classmethod
    async def price_urls_by_type(cls, urls: list[str]) -> dict:
        """ This function organizes price and promo URLs by type for selected supermarket store. """
        types = ["PromoFull", "Promo", "PriceFull", "Price"]
        urls_by_type_dict = {t: [] for t in types}
        for url in urls:
            for t in types:
                if t in url:
                    urls_by_type_dict[t].append(url)
                    break
        return urls_by_type_dict

    @classmethod
    async def get_price_files(cls):
        """
        Function to get all price/pricefull and promo/promofull urls from site
        Helper function for prices function
        """
        tasks = {}
        async with httpx.AsyncClient() as client:
            async with asyncio.TaskGroup() as tg:
                # file types 1 and 2
                for file_type in (1, 2):
                    tasks[file_type] = tg.create_task(cls.get_files(file_type=file_type, client=client))

        # TaskGroup completed → safe to read results
        urls = []

        for file_type, task in tasks.items():
            result = task.result()  # ❗ This is the returned dict from get_files()
            urls.extend(result["response"])

        return {'response': urls}

    @classmethod
    async def prices(cls, store_code: int | str):
        """ This function gets price and promo files for hazihinam supermarket chain. """
        try:
            # Get all file links
            file_links = await cls.get_price_files()

            all_urls = file_links.get('response', [])
            # Filter price and promo files for the selected store
            price_urls = [url for url in all_urls if int(url.split('-')[2]) == int(store_code)]
            # Organize Urls by type and get latest for each type
            price_urls_dict = await cls.price_urls_by_type(price_urls)
            for key in price_urls_dict.keys():
                if price_urls_dict[key]:
                    price_urls_dict[key] = await cls.latest(price_urls_dict[key])
                else:
                    price_urls_dict[key] = None
            return price_urls_dict
        except Exception as e:
            return {'Error': str(e)}

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
            stores.append(await cls.as_store_dict(s, **chain_info, subchain_code=sub.get("SubChainID")
                                                  , subchain_name=sub.get("SubChainName")))
        return {'stores_data_list': stores}

    @classmethod
    async def search_for_item(cls, price_data: dict, search_term: str):
        """ Return dicts that has search term """
        return [d for d in price_data if search_term in d['ItemName']]

    @classmethod
    def promo_blacklist(cls) -> set[str]:
        """ Return list of promo blacklist PromotionId's - General promos that should be ignored """
        return set()  # When blacklist the format should be: {"4305214"}
