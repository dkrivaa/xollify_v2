import httpx
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin

from backend.app.utilities.url_request import url_request
from backend.app.core.super_class import SupermarketChain


class LaibCatalog(SupermarketChain):
    abstract = True

    @classmethod
    async def parse_response(cls, response: bytes) -> list[str | None]:
        """ This function parses the HTML response using BeautifulSoup. """
        # class info
        base = await cls.get_url()
        soup = BeautifulSoup(response, "lxml")
        # Find the table inside the div with id="download_content"
        rows = soup.select("#download_content table tr")[1:]
        # Extract all hrefs from <a> tags inside that table
        hrefs = []
        for row in rows:
            a = row.find("a", href=True)
            if a and not a["href"].startswith("javascript:"):
                href = a["href"].replace("\\", "/")  # normalize slashes
                hrefs.append(urljoin(base, href))
        return hrefs

    @classmethod
    async def chain_links(cls, urls: list[str]) -> list[str]:
        """ This function gets chain links from all laibcatalog link for selected supermarket chain. """
        code = await cls.get_code()
        return [url for url in urls if code in url]

    @classmethod
    async def all_urls_for_chain(cls, client: httpx.AsyncClient | None = None) -> list | dict:
        """ This function gets store list for laibcatalog supermarket chains. """
        base = await cls.get_url()
        # Get store list
        try:
            # Get response from the URL
            response = await url_request(base, client=client, )
            # Parse the response to extract store links
            all_links = await cls.parse_response(response['response'])
            all_for_chain = await cls.chain_links(all_links)
            return {'urls': all_for_chain}
        except httpx.HTTPStatusError as e:
            return {'Error': f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {'Error': f"Request error: {str(e)}"}

    @classmethod
    async def get_latest(cls, urls: list[str]) -> str:
        """ Get the latest file from a given list of URLs. """
        def extract_date(url: str):
            return url.split('/')[-1].split('-')[2]
        return max(urls, key=lambda url: extract_date(url))

    @classmethod
    async def extract_store_code(cls, url: str) -> int:
        """ This function extracts store code from laibcatalog URL. """
        return int(url.split('/')[-1].split('-')[1])

    @classmethod
    async def stores(cls, client: httpx.AsyncClient | None = None) -> dict:
        """ This function gets store list for selected laibcatalog supermarket chain. """
        all_urls = await cls.all_urls_for_chain(client=client)
        # If no errors:
        if 'Error' not in all_urls.keys():
            store_urls = [url for url in all_urls['urls'] if 'store' in url.lower()]
            if len(store_urls) == 1:
                return {'stores': store_urls[0]}
            elif len(store_urls) > 1:
                return {'stores': await cls.get_latest(store_urls)}
        else:
            return all_urls

    @classmethod
    async def prices_for_store(cls, store_code: int | str) -> dict:
        """ This function gets price and promo files for selected laibcatalog supermarket chain. """
        # All urls for the chain
        all_urls = await cls.all_urls_for_chain()
        # If no errors:
        if 'Error' not in all_urls.keys():
            # Price and promo files for the selected store
            store_urls = [url for url in all_urls['urls'] if await cls.extract_store_code(url) == int(store_code)]
            return {'prices': store_urls}
        else:
            return all_urls

    @classmethod
    async def price_urls_by_type(cls, urls: list[str]) -> dict:
        """ This function organizes price and promo URLs by type for selected laibcatalog supermarket chain. """
        types = ["PromoFull", "Promo", "PriceFull", "Price"]
        urls_by_type_dict = {t: [] for t in types}
        for url in urls:
            for t in types:
                if t in url:
                    urls_by_type_dict[t].append(url)
                    break
        return urls_by_type_dict

    @classmethod
    async def prices(cls, store_code: int | str) -> dict:
        """ This function gets price and promo files for selected laibcatalog supermarket chain. """
        # Get price URLs for the selected store
        all_urls = await cls.prices_for_store(store_code)
        # No errors
        if 'Error' not in all_urls.keys():
            urls_by_type = await cls.price_urls_by_type(all_urls['prices'])
            result = {}
            for key in urls_by_type.keys():
                latest_url = await cls.get_latest(urls_by_type[key]) if urls_by_type[key] else None
                if latest_url is not None:
                    result[key] = latest_url
            return result
        else:
            return all_urls

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """
        This function extracts store data from the stores_data_dict extracted from latest stores url
        and prepares it for database insertion.
        """
        branches = stores_data_dict.get("Store", {}).get('Branches', {})
        branch = branches.get("Branch", {})

        stores = []
        for b in branch:
            stores.append(await cls.as_store_dict(b,))
        return {'stores_data_list': stores}

    @classmethod
    async def search_for_item(cls, price_data: dict, search_term: str):
        """ Return dicts that has search term """
        return [d for d in price_data if search_term in d['ItemName']]

    @classmethod
    def promo_blacklist(cls) -> set[str]:
        """ Return list of promo blacklist PromotionId's - General promos that should be ignored """
        return set()  # When blacklist the format should be: {"4305214"}


class Victory(LaibCatalog):
    abstract = False
    name = 'ויקטורי רשת סופרמרקטים בע"מ'
    alias = 'victory'
    chain_code = '7290696200003'
    url = 'https://laibcatalog.co.il/'
    link_type = 'laibcatalog'


class HCohen(LaibCatalog):
    abstract = False
    name = 'ח. כהן סוכנות מזון ומשקאות בע"מ'
    alias = 'hcohen'
    chain_code = '7290455000004'
    url = 'https://laibcatalog.co.il/'
    link_type = 'laibcatalog'


class KnMarket(LaibCatalog):
    abstract = False
    name = 'כ.נ מחסני השוק בע"מ'
    alias = 'knmarket'
    chain_code = '7290661400001'
    url = 'https://laibcatalog.co.il/'
    link_type = 'laibcatalog'

