from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Index, Boolean, Text

# Define SQLAlchemy ORM model for stores and items

Base = declarative_base()


class Store(Base):
    """ Class representing a store in the database. All chains in one table. """
    __tablename__ = "stores"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Chain info
    chain_code = Column(String, nullable=False)  # always provided
    chain_name = Column(String, nullable=True)  # optional if XML has it
    subchain_code = Column(String, nullable=True)
    subchain_name = Column(String, nullable=True)

    # Store info
    store_code = Column(String, nullable=False)  # always provided
    store_name = Column(String, nullable=True)
    store_type = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    zipcode = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_chain_code", "chain_code"),
        Index("ix_chain_store", "chain_code", "store_code", unique=True),
    )


class Item(Base):
    """ Class representing item """
    __tablename__ = 'items'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Chain and store info
    chain_code = Column(String, nullable=False)
    store_code = Column(String, nullable=False)

    # Item info
    price_update_date = Column(String, nullable=False)  # always provided
    item_code = Column(String, nullable=False)
    item_type = Column(String, nullable=True)
    item_name = Column(String, nullable=False)
    manufacturer_name = Column(String, nullable=False)
    manufacture_country = Column(String, nullable=True)
    manufacturer_item_description = Column(String, nullable=False)
    unit_qty = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    bIs_weighted = Column(String, nullable=False)
    unit_of_measure = Column(String, nullable=False)
    qty_in_package = Column(String, nullable=False)
    item_price = Column(String, nullable=False)
    unit_of_measure_rice = Column(String, nullable=False)
    allow_discount = Column(String, nullable=False)
    item_status = Column(String, nullable=False)
    item_id = Column(String, nullable=True)
    chain_alias = Column(String, nullable=False)

    __table_args__ = (
        Index('ix_item_code', 'item_code', unique=True),
    )

