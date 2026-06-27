# inventory (multi-file)

Implement two files so the tests pass.

`models.py`:
- A `Product` class constructed as `Product(sku, price, qty)` exposing attributes
  `sku` (str), `price` (float), `qty` (int).

`inventory.py`:
- `total_value(products)` — sum of `price * qty` across a list of `Product`,
  returned as a float.
- `restock(products, sku, amount)` — find the product whose `sku` matches,
  increase its `qty` by `amount`, and return that product. If no product
  matches, return `None`.
