"""Simple domain models used by the inventory application."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    product_id: int
    name: str
    description: str
    price: Decimal
    stock_quantity: int
    reorder_level: int


@dataclass
class OrderLine:
    product_id: int
    quantity: int
