import httpx
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext
from datetime import datetime
import re
import asyncio
from backend.app.core.super_class import SupermarketChain


class PublishedPrices(SupermarketChain):
    abstract = True

    @classmethod
    async def crawl_files(cls, ):
        """
        This function crawls files for publishedprices supermarket chains and returns a dict with:
        -cookies
        -list of all file links
        """
        # Get login details for chain
        url = getattr(cls, 'url', '')
        target_url = f'{url[:-5]}file'
        username = getattr(cls, 'username', '')
        password = getattr(cls, 'password', '')

        if username == 'yuda_ho':
            target_url = f'{target_url}/d/Yuda/'

        browser_config = BrowserConfig(
            headless=True,
        )

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            delay_before_return_html=5,
            session_id="hn_session"
        )

        crawler = AsyncWebCrawler(config=browser_config)

        result_holder = {}

        async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
            # Called right after a new page + context are created (ideal for auth or route config).
            print("[HOOK] on_page_context_created - Setting up page & context.")

            # Go to login page
            await page.goto(url)
            # Fill credentials and press submit
            await page.fill("input[name='username']", username)
            await page.fill("input[name='password']", password)  # if required
            await page.click("button[type='submit']")
            # Wait for redirect after login
            await page.wait_for_load_state("networkidle", timeout=80000)
            # If redirect is not the target url with files
            if page.url != target_url:
                # Go to target url
                await page.goto(target_url)
                # Wait for redirect
                await page.wait_for_load_state("networkidle", timeout=80000)

            # On page with files:
            # Get cookies
            result_holder['cookies'] = await context.cookies()
            # Convert Playwright cookies (list of dicts) to a requests-compatible dict
            result_holder['cookies'] = cls.playwright_cookies_to_requests(result_holder['cookies'])

            all_links = []
            # 1️⃣ Try to set the rows-per-page dropdown to 1000
            select = page.locator("select[name='fileList_length']")
            try:
                await select.select_option("1000")
                # Wait for table to refresh
                await page.wait_for_timeout(1000)  # short wait for JS
            except Exception:
                # If "1000" is not an option, skip
                pass

            while True:
                # 2️⃣ Collect links on the current page
                links = await page.eval_on_selector_all(
                            "table a.f",
                            "els => els.map(e => e.href)"
                        )
                all_links.extend(links)

                # 3️⃣ Check if "Next" button is disabled
                next_li = page.locator("li#fileList_next")
                class_name = await next_li.get_attribute("class")
                if "disabled" in class_name:
                    break  # no more pages

                # 4️⃣ Click Next and wait for table to redraw
                await next_li.locator("a").click()
                await page.wait_for_timeout(1000)  # adjust if needed

            result_holder['links'] = all_links

        # Run the hook and the crawler
        crawler.crawler_strategy.set_hook(
            "on_page_context_created", on_page_context_created
        )

        try:
            await crawler.start()
            await crawler.arun(target_url, config=crawler_config)
            return result_holder

        finally:
            await crawler.close()

    @classmethod
    def playwright_cookies_to_requests(cls, playwright_cookies):
        """
        Convert Playwright cookies (list of dicts) to a requests-compatible dict
        """
        return {c['name']: c['value'] for c in playwright_cookies if 'name' in c and 'value' in c}

    @classmethod
    async def stores(cls, client: httpx.AsyncClient | None = None) -> dict:
        """
        This function gets latest store list for publishedprices supermarket chain class.
        """
        result_holder = await cls.crawl_files()
        all_links = result_holder.get('links', [])

        if all_links:
            latest_store_url = max(
                (u for u in all_links if re.search(r'(\d{8}-\d{6})\.xml$', u)),
                key=lambda u: datetime.strptime(re.search(r'(\d{8}-\d{6})\.xml$', u).group(1), "%Y%m%d-%H%M%S"),
                default=None
            )
            if not latest_store_url:
                latest_store_url = max(
                    (
                        u for u in all_links
                        if re.search(r'Stores\d+-\d{12}\.xml$', u)
                    ),
                    key=lambda u: datetime.strptime(
                        re.search(r'(\d{12})\.xml$', u).group(1), "%Y%m%d%H%M"
                    ),
                    default=None
                )

        else:
            # If no links found
            latest_store_url = None

        return {'stores': latest_store_url, 'cookies': result_holder.get('cookies', {})}

    @classmethod
    def pattern(cls):
        """
        Helper function that defines pattern of file name - store code and date
        Works for most chains, and overwriten in chains with different patterns
        """
        return re.compile(
                r"/file/d/(PriceFull|Price|PromoFull|Promo)\d+(?:-\d+)*-(\d+)-(\d{8})-?(\d{4,6})"
            )


    @classmethod
    async def prices(cls, store_code: int | str) -> dict:
        """
        This function gets price and promo files for publishedprices supermarket chain class.
        """
        result_holder = await cls.crawl_files()
        all_links = result_holder.get('links', [])

        def get_latest_file(urls: list[str], store_code: int | str) -> dict:
            """
                Given a list of URLs from publishedprices.co.il and a specific store code (e.g., '001'),
                return a dict mapping each file type ('Price', 'PriceFull', 'Promo', 'PromoFull')
                to the latest URL for that store.
                """
            pattern = cls.pattern()

            latest = {}

            for url in urls:
                match = pattern.search(url)
                if not match:
                    continue

                file_type, code_str, date, time = match.groups()
                code = int(code_str)  # convert to int
                if code != store_code:
                    continue  # skip other stores

                time = time.ljust(6, "0")  # ensure HHMMSS format
                dt = datetime.strptime(date + time, "%Y%m%d%H%M%S")

                # Keep only the latest datetime per file type
                if file_type not in latest or dt > latest[file_type]["dt"]:
                    latest[file_type] = {"url": url, "dt": dt}

            # Return simplified mapping: file_type -> url
            return {file_type.lower(): data["url"] for file_type, data in latest.items()}

        # Get price and promo files for the specified store
        result = get_latest_file(all_links, store_code=int(store_code))

        result['cookies'] = result_holder.get('cookies', {})

        return result

    @classmethod
    async def extract_stores_data_for_db_type1(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
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
    async def extract_stores_data_for_db_type2(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """
        This function extracts store data from the stores_data_dict extracted from latest stores url
        and prepares it for database insertion.
        """
        root = stores_data_dict.get("Root", {})
        sub = root.get("SubChains", {}).get("SubChain", [])
        chain_info = {
            "chain_code": root.get("ChainID"),
            "chain_name": root.get("ChainName"),
        }

        stores = []
        for s in sub:
            for store in s.get("Stores", {}).get("Store", []):
                stores.append(await cls.as_store_dict(store, **chain_info,
                                                      subchain_code=s.get("SubChainID"),
                                                      subchain_name=s.get("SubChainName")))
        return {'stores_data_list': stores}

    @classmethod
    async def search_for_item(cls, price_data: dict, search_term: str):
        """ Return dicts that has search term """
        return [d for d in price_data if search_term in d['ItemName']]

    @classmethod
    def promo_blacklist(cls) -> set[str]:
        """ Return list of promo blacklist PromotionId's - General promos that should be ignored """
        return set()  # When blacklist the format should be: {"4305214"}


class RamiLevi(PublishedPrices):
    abstract = False
    name = 'רשת חנויות רמי לוי שיווק השקמה 2006 בע"מ'
    chain_code = '7290058140886'
    alias = 'ramilevi'
    url = 'https://url.publishedprices.co.il/login'
    username = 'RamiLevi'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class DorAlon(PublishedPrices):
    abstract = False
    name = 'דור אלון ניהול מתחמים קמעונאיים בע"מ'
    alias = 'doralon'
    chain_code = '7290492000005'
    url = 'https://url.publishedprices.co.il/login'
    username = 'doralon'
    link_type = 'publishedprices'

    @classmethod
    def pattern(cls):
        """ Overwriting the pattern for PublishedPrices class """
        return re.compile(
            r"(Price|Promo|PriceFull|PromoFull)\d+-\d+-(\d+)-(\d{8})-(\d{6})\.gz"
        )

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type2(stores_data_dict)


class TivTaam(PublishedPrices):
    abstract = False
    name = 'טיב טעם רשתות בע"מ'
    alias = 'tivtaam'
    chain_code = '7290873255550'
    url = 'https://url.publishedprices.co.il/login'
    username = 'TivTaam'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class Yochananof(PublishedPrices):
    abstract = False
    name = 'מ. יוחננוף ובניו (1988) בע"מ'
    alias = 'yohananof'
    chain_code = '7290803800003'
    url = 'https://url.publishedprices.co.il/login'
    username = 'yohananof'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class OsherAd(PublishedPrices):
    abstract = False
    name = 'מרב-מזון כל בע"מ (אושר עד)'
    alias = 'osherad'
    chain_code = '7290103152017'
    url = 'https://url.publishedprices.co.il/login'
    username = 'osherad'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class SalahDabah(PublishedPrices):
    abstract = False
    name = 'סאלח דבאח ובניו בע"מ'
    alias = 'salahdabah'
    chain_code = '7290526500006'
    url = 'https://url.publishedprices.co.il/login'
    username = 'SalachD'
    password = '12345'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class StopMarket(PublishedPrices):
    abstract = False
    name = 'סטופ מרקט בע"מ'
    alias = 'stopmarket'
    chain_code = '7290639000004'
    url = 'https://url.publishedprices.co.il/login'
    username = 'Stop_Market'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class Politzer(PublishedPrices):
    abstract = False
    name = 'פוליצר חדרה (1982) בע"מ'
    alias = 'politzer'
    chain_code = '7291059100008'
    url = 'https://url.publishedprices.co.il/login'
    username = 'politzer'
    link_type = 'publishedprices'

    @classmethod
    def pattern(cls):
        """ Overwriting the pattern for PublishedPrices class """
        return re.compile(
            r"(Price|Promo|PriceFull|PromoFull)\d+-\d+-(\d+)-(\d{8})-(\d{6})\.gz"
        )

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


# class SuperYuda(PublishedPrices):
#     abstract = False
#     name = 'סופר יודה'
#     alias = 'superyuda'
#     chain_code = '7290058177776'
#     url = 'https://publishedprices.co.il/login'
#     username = 'yuda_ho'
#     password = 'Yud@147'
#     link_type = 'publishedprices'
#
#     @classmethod
#     def pattern(cls):
#         """
#         Helper function that defines pattern of file name - store code and date
#         Works for most chains, and overwriten in chains with different patterns
#         """
#         return re.compile(
#             r"/file/d/Yuda/(PriceFull|Price|PromoFull|Promo)\d+-(\d+)-(\d{8})(\d{4,6})"
#         )

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


# class FreshMarket(PublishedPrices):
#     abstract = False
#     name = 'פרשמרקט'
#     alias = 'freshmarket'
#     chain_code = '7290876100000'
#     url = 'https://url.publishedprices.co.il/login'
#     username = 'freshmarket'
#     link_type = 'publishedprices'
#
#     @classmethod
#     async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
#         """ Define what schema to use for extracting stores data for chain """
#         return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class KeshetTaamim(PublishedPrices):
    abstract = False
    name = 'קשת טעמים בע"מ'
    alias = 'keshettaamim'
    chain_code = '7290785400000'
    url = 'https://url.publishedprices.co.il/login'
    username = 'Keshet'
    link_type = 'publishedprices'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


# class SuperCofix(PublishedPrices):
#     abstract = False
#     name = 'סופר קופיקס'
#     alias = 'supercofix'
#     chain_code = '7291056200008'
#     url = 'https://url.publishedprices.co.il/login'
#     username = 'SuperCofixApp'
#     link_type = 'publishedprices'
#
#     @classmethod
#     async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
#         """ Define what schema to use for extracting stores data for chain """
#         return await cls.extract_stores_data_for_db_type1(stores_data_dict)


