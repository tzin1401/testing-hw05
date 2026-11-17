#!/usr/bin/env python3
"""Generate workflow CSVs from users.csv and the running SUT's product API."""
import csv
import json
import math
from pathlib import Path
from urllib.request import urlopen

DATA = Path(__file__).resolve().parent.parent / "data"

with (DATA / "users.csv").open(newline="", encoding="utf-8") as f:
    users = list(csv.DictReader(f))
if len(users) != 300 or any(
    user.get("email") != f"perf{i:03d}@eshop.com" or not user.get("password")
    for i, user in enumerate(users, 1)
):
    raise ValueError("users.csv must contain perf001..perf300 in order with passwords")

with (DATA / "products.csv").open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    if not reader.fieldnames or not {"product_id", "keyword", "quantity"} <= set(reader.fieldnames):
        raise ValueError("products.csv is missing required columns")
    products = list(reader)
if len(products) != 5 or len({row["product_id"] for row in products}) != 5:
    raise ValueError("products.csv must contain five distinct products")

with urlopen("http://localhost:3000/api/products", timeout=10) as response:
    api_products = json.load(response)
if not isinstance(api_products, list):
    raise ValueError("product API did not return an array")
by_id = {str(product["id"]): product for product in api_products}
for row in products:
    product = by_id[row["product_id"]]
    price, name = product["price"], product["name"]
    if not name or not math.isfinite(float(price)) or float(price) <= 0:
        raise ValueError(f"invalid API product: {row['product_id']}")
    row["price"], row["name"] = price, name

for filename, rows in (
    ("users_main.csv", [{"email": u["email"], "password": u["password"]} for u in users[:290]]),
    ("users_lock.csv", [{"email": u["email"], "password": "WrongPass1!"} for u in users[290:]]),
):
    with (DATA / filename).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "password"])
        writer.writeheader()
        writer.writerows(rows)

with (DATA / "products.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["product_id", "keyword", "quantity", "price", "name"], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(products)
print("Generated 290 main users, 10 lockout users, and 5 products.")
