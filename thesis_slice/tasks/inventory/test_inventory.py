from models import Product
from inventory import total_value, restock


def _sample():
    return [Product("A", 2.0, 3), Product("B", 5.0, 1)]


def test_product_attributes():
    p = Product("X", 1.5, 4)
    assert (p.sku, p.price, p.qty) == ("X", 1.5, 4)


def test_total_value():
    assert total_value(_sample()) == 11.0


def test_restock_existing():
    products = _sample()
    p = restock(products, "A", 5)
    assert p.qty == 8
    assert total_value(products) == 21.0


def test_restock_missing():
    assert restock(_sample(), "Z", 5) is None
