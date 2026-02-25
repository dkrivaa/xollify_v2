

class SupermarketChain:
    """ The parent class for all supermarket chains """
    registry = []  # holds all subclasses automatically

    def __init_subclass__(cls, **kwargs):
        """Automatically register any subclass."""
        super().__init_subclass__(**kwargs)
        if cls is not SupermarketChain and not getattr(cls, 'abstract', False):  # avoid registering the abstract base itself
            SupermarketChain.registry.append(cls)

    ##### Class methods that MUST be implimented by all subclasses
    @classmethod
    async def stores(cls, ):
        """
        This function gets latest store url for the supermarket chain.
        Return value: {stores: url}
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    async def prices(cls, store_code: int | str, ):
        """
        This function gets latest price and promo urls for relevant store for the supermarket chain.
        Return value: {price: url, pricefull: url, promo: url, promofull: url}
        """
        raise NotImplementedError("Subclasses must implement this method.")

    ### Other general class methods
    @classmethod
    async def safe_prices(cls, store_code: int | str, ):
        """ Wrapper for prices() that returns None if prices() raises an exception """
        try:
            return await cls.prices(store_code)
        except Exception as e:
            msg = f"Error getting prices for {cls.alias} store {store_code}. Please try again in a few minutes."
            print(f'{msg} + {e}')
            return None

    @classmethod
    async def get_code(cls):
        """ Returns the code of the supermarket chain """
        return getattr(cls, 'chain_code', None)

    @classmethod
    async def get_alias(cls):
        """ Returns the code of the supermarket chain """
        return getattr(cls, 'alias', None)

    @classmethod
    async def get_url(cls):
        """ Returns the url of the supermarket chain """
        return getattr(cls, 'url', None)

    @classmethod
    async def get_link_type(cls):
        """ Returns the link type of the supermarket chain """
        return getattr(cls, 'link_type', None)

    @classmethod
    async def get_username(cls):
        """ Returns the username of the supermarket chain """
        return getattr(cls, 'username', None)

    @classmethod
    async def get_password(cls):
        """ Returns the password of the supermarket chain """
        return getattr(cls, 'password', None)

    @classmethod
    async def as_store_dict(cls, s: dict, **extra) -> dict:
        """Utility to standardize store output."""
        return {
            "chain_code": extra.get('chain_code') or await cls.get_code(),
            "chain_name": await cls.get_alias(),
            "subchain_code": extra.get('subchain_code') or s.get("SubChainID") or s.get("SUBCHAINID") or s.get(
                "SubChainId"),
            "subchain_name": extra.get('subchain_name') or s.get("SubChainName") or s.get("SUBCHAINNAME"),
            "store_code": s.get("StoreID") or s.get("STOREID") or s.get("StoreId"),
            "store_name": s.get("StoreName") or s.get("STORENAME"),
            "store_type": s.get("StoreType") or s.get("STORETYPE"),
            "address": s.get("Address") or s.get("ADDRESS"),
            "city": s.get("City") or s.get("CITY"),
            "zipcode": s.get("ZipCode") or s.get("ZIPCODE") or s.get("ZIPCode"),
        }

    @classmethod
    def get_price_data(cls, price_data: dict):
        """ Extract the list of prices from task.result() """
        items = (price_data.get("Root") or price_data.get("root"))["Items"]["Item"]
        for item in items:
            item["ChainAlias"] = cls.alias

        return items

    @classmethod
    def get_shopping_prices(cls, price_data: dict, shoppinglist: list[str | int]) -> dict:
        """ Getting prices for barcodes in shopping list """
        results = {}
        for barcode in shoppinglist:
            results[str(barcode)] = next((d for d in price_data if d['ItemCode'] == str(barcode)), None)

        return results

    @classmethod
    def get_promo_data(cls, promo_data: dict):
        """ Extract the list of prices from task.result() """
        items = (promo_data.get("Root") or promo_data.get("root"))["Promotions"]["Promotion"]
        for item in items:
            item["ChainAlias"] = cls.alias

        return items

    @classmethod
    def get_shopping_promos(cls, promo_data: list[dict], shoppinglist: list[str | int],
                            blacklist: set) -> dict:
        """ Getting promos for barcodes in shopping list """
        # Dict to hold results
        results = {}

        for barcode in shoppinglist:
            barcode = str(barcode)
            # A list to hold matched promos for the barcode
            matched_promos = []

            for promo in promo_data:
                items = promo.get("PromotionItems", {}).get("Item", [])

                # Normalize: dict → list
                if isinstance(items, dict):
                    items = [items]

                if any(item.get("ItemCode") == barcode for item in items):
                    matched_promos.append(promo)

            # Blacklist of PromotionIds to exclude (General promos)
            try:
                matched_promos = [
                    promo for promo in matched_promos
                    if str(promo.get("PromotionId", "")).strip() not in blacklist
                ]
            except Exception:
                pass

            # Make dict with barkide as key and list of matched promos as value
            results[barcode] = matched_promos

        return results

    @classmethod
    def promo_audience(cls, promo: dict) -> str | None:
        """ Return the audience of the promo if exists """
        # Possible audiences:
        audiences = {
            '0': 'All Customers',
            '1': 'Club Members',
            '2': 'Creditcart Holders',
            '3': 'Other / Unspecified',
        }
        return audiences[promo.get('Clubs').get('ClubId', 'Unspecified')]

