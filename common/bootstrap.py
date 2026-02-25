""" This is used to initialize registry of all chains at startup """

from common.core.binaprojects import BinaProjects
from common.core.carrefour import CarrefourParent
# from common.core.hazihinam import HaziHinam
# from common.core.laibcatalog import LaibCatalog
from common.core.publishedprices import PublishedPrices
from common.core.shufersal import Shufersal
from common.core.super_class import SupermarketChain


def initialize_backend():
    """
    Call this once at app startup.
    Ensures all supermarket chains subclasses are imported and registered.
    """
    pass



