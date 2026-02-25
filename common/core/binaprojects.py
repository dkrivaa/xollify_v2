import httpx
from datetime import datetime, timedelta
import json

from backend.app.utilities.url_request import url_request
from backend.app.core.super_class import SupermarketChain


class BinaProjects(SupermarketChain):
    abstract = True

    @classmethod
    async def get_file(cls, file_type: int = 0, store: int = 0, date: str | None = None,
                       client: httpx.AsyncClient | None = None) -> dict:
        """
        Asynchronously get defined files for Binaproject supermarket chains.

        :param chain_code: Chain code identifying the supermarket chain.
        :param session: (Ignored) for backward compatibility.
        :param file_type: 0-all, 1-stores, 2-prices, 3-promo, 4-pricefull, 5-promofull.
        :param store: store code.
        :param date: specific date string (DD/MM/YYYY), otherwise today.
        :param client: Optional pre-configured httpx.AsyncClient.
        :return: JSON dict of relevant files or error message.
        """
        base_url = await cls.get_url()
        base_url = base_url[:-9]  # Remove last 9 characters
        url = f"{base_url}MainIO_Hok.aspx"

        # Determine start date
        current_date = (
            datetime.today() if date is None else datetime.strptime(date, "%d/%m/%Y")
        )

        # Loop backward until we find data
        today = datetime.today()
        while current_date > today - timedelta(days=14):
            date_str = current_date.strftime("%d/%m/%Y")
            payload = {
                "WStore": str(store),
                "WDate": date_str,
                "WFileType": str(file_type),
            }
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
            result = await url_request(url, method="POST", payload=payload, headers=headers, client=client)

            # Handle response or error
            if "Error" in result:
                return result  # Return immediately on HTTP/network error

            try:
                data = result["response"]
                json_data = json.loads(data)
                if json_data:  # non-empty list
                    return {'response': json_data}
            except Exception as e:
                return {"Error": f"Invalid JSON response: {str(e)}"}

            # If no file for date, go back one day
            current_date -= timedelta(days=1)

        return {"Error": "No files found in the last 14 days."}

    @classmethod
    async def latest_file(cls, data: list[dict]) -> dict:
        """ This function gets the latest file in list of dicts of files from binaprojects site """
        try:
            latest_row = max(
                data,
                key=lambda row: datetime.strptime(row['DateFile'], "%H:%M %d/%m/%Y"
                ),
            )
            return latest_row
        except Exception as e:
            return {"Error": f"Error determining latest file: {str(e)}"}

    @classmethod
    async def stores(cls, client: httpx.AsyncClient | None = None):
        """ This function gets store list for binaprojects supermarket chain. """
        try:
            # Get links for store files (file_type=1)
            store_links = await cls.get_file(file_type=1, client=client)
            # From response, get the latest store file
            latest = await cls.latest_file(store_links['response'])
            # Construct full download URL
            base_url = await cls.get_url()
            base_url = base_url[:-9]
            latest_url = f"{base_url}Download/{latest['FileNm']}"
            return {'stores': latest_url}
        except Exception as e:
            return {'Error': str(e)}

    @classmethod
    async def prices(cls, store_code: int | str):
        types = {'prices': 2, 'promo': 3, 'pricefull': 4, 'promofull': 5}
        try:
            prices = {}
            for t, ft in types.items():
                # Get links for file type
                file_links = await cls.get_file(file_type=ft, store=store_code)
                # From response, get the latest store file
                latest = await cls.latest_file(file_links['response'])
                base_url = await cls.get_url()
                base_url = base_url[:-9]
                # Construct full download URL
                latest_url = f"{base_url}Download/{latest['FileNm']}"
                prices[t] = latest_url
            return prices
        except Exception as e:
            return {'Error': str(e)}

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
            stores.append(await cls.as_store_dict(s, **chain_info, subchain_code=sub.get("SubChainId")
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
                if isinstance(store, str):
                    continue
                stores.append(await cls.as_store_dict(store, **chain_info,
                                                      subchain_code=s.get("SubChainId"),
                                                      subchain_name=s.get("SubChainName")))
        return {'stores_data_list': stores}

    @classmethod
    async def search_for_item(cls, price_data: dict, search_term: str):
        """ Return dicts that has search term """
        return [d for d in price_data if search_term in d['ItemNm']]

    @classmethod
    def promo_blacklist(cls) -> set[str]:
        """ Return list of promo blacklist PromotionId's - General promos that should be ignored """
        return set()  # When blacklist the format should be: {"4305214"}

    @classmethod
    def promo_audience(cls, promo: dict) -> str | None:
        """ Return the audience of the promo if exists - special for binaprojects """
        # Posible audiences:
        audiences = {
            '0': 'All Customers',
            '1': 'Club Members',
            '2': 'Creditcart Holders',
            '3': 'Other / Unspecified',
        }
        return audiences[promo.get('AdditionalRestrictions').get('Clubs').get('ClubId', 'Unspecified')]


class KingStore(BinaProjects):
    abstract = False
    name = 'אלמשהדאוי קינג סטור בע"מ'
    alias = 'kingstore'
    chain_code = '7290058108879'
    url = 'https://kingstore.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class Maayan2000(BinaProjects):
    abstract = False
    name = 'ג.מ מעיין אלפיים (07) בע"מ'
    alias = 'maayan2000'
    chain_code = '7290058159628'
    url = 'https://maayan2000.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class GoodPharm(BinaProjects):
    abstract = False
    name = 'גוד פארם בע"מ'
    alias = 'goodpharm'
    chain_code = '7290058197699'
    url = 'https://goodpharm.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class ZulvbGadol(BinaProjects):
    abstract = False
    name = 'זול ובגדול בע"מ'
    alias = 'zulvbgadol'
    chain_code = '7290058173198'
    url = 'https://zolvebegadol.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class SuperSapir(BinaProjects):
    abstract = False
    name = 'סופר ספיר בע"מ'
    alias = 'supersapir'
    chain_code = '7290058156016'
    url = 'https://supersapir.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type2(stores_data_dict)


class CityMarket(BinaProjects):
    abstract = False
    name = 'סיטי מרקט'
    alias = 'citymarket'
    chain_code = '7290058266241'
    url = 'https://citymarketkiryatgat.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class SuperBareket(BinaProjects):
    abstract = False
    name = 'עוף והודו ברקת - חנות המפעל בע"מ'
    alias = 'superbareket'
    chain_code = '7290875100001'
    url = 'https://superbareket.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type2(stores_data_dict)


class KT(BinaProjects):
    abstract = False
    name = 'קיי.טי. יבוא ושיווק בע"מ (משנת יוסף)'
    alias = 'kt'
    chain_code = '5144744100001'
    url = 'https://ktshivuk.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class ShukHayir(BinaProjects):
    abstract = False
    name = 'שוק העיר (ט.ע.מ.ס) בע"מ'
    alias = 'shukhayir'
    chain_code = '7290058148776'
    url = 'https://shuk-hayir.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)


class ShefaBirkatHashem(BinaProjects):
    abstract = False
    name = 'שפע ברכת השם בע"מ'
    alias = 'shefabirkathashem'
    chain_code = '7290058134977'
    url = 'https://shefabirkathashem.binaprojects.com/Main.aspx'
    link_type = 'binaprojects'

    @classmethod
    async def extract_stores_data_for_db(cls, stores_data_dict: dict) -> dict[str, list[dict]]:
        """ Define what schema to use for extracting stores data for chain """
        return await cls.extract_stores_data_for_db_type1(stores_data_dict)