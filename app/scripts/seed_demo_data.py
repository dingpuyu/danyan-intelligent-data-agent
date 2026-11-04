"""Seed deterministic demo data for local retrieval and SQL evaluation.

The script only adds rows whose IDs start with ``DEMO``/``DP``/``DR``/``DC``
and is safe to run repeatedly.  It is intentionally separate from the SQL
bootstrap files so a clean install can keep the small teaching dataset while
local evaluation can opt into a larger, reproducible workload.
"""

import asyncio
import os
import random
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


DB_URL = (
    "mysql+asyncmy://{user}:{password}@{host}:{port}/{database}"
)


def _db_url() -> str:
    user = os.getenv("DW_DB_USER", "danyan")
    password = os.getenv("DW_DB_PASSWORD", "Danyan.dev.123")
    host = os.getenv("DW_DB_HOST", "127.0.0.1")
    port = os.getenv("DW_DB_PORT", "3306")
    return DB_URL.format(user=user, password=password, host=host, port=port, database="dw")


def _rows(seed: int, order_count: int, product_count: int, region_count: int, customer_count: int):
    rng = random.Random(seed)
    regions = []
    region_names = ["华东", "华南", "华北", "华中", "西南", "西北"]
    provinces = ["浙江省", "广东省", "北京市", "湖北省", "四川省", "陕西省"]
    for i in range(1, region_count + 1):
        regions.append({
            "region_id": f"DR{i:04d}",
            "province": provinces[(i - 1) % len(provinces)],
            "region_name": region_names[(i - 1) % len(region_names)],
            "country": "中国",
        })

    customers = []
    levels = ["青铜", "白银", "黄金", "铂金"]
    for i in range(1, customer_count + 1):
        customers.append({
            "customer_id": f"DC{i:05d}",
            "customer_name": f"演示客户{i:04d}",
            "gender": "男" if i % 2 else "女",
            "member_level": levels[(i - 1) % len(levels)],
        })

    products = []
    categories = [("手机数码", "青竹"), ("家用电器", "峰谷"), ("食品饮料", "山海"), ("服饰", "云杉"), ("户外运动", "远行")]
    for i in range(1, product_count + 1):
        category, brand = categories[(i - 1) % len(categories)]
        products.append({
            "product_id": f"DP{i:05d}",
            "product_name": f"演示商品{i:03d}",
            "category": category,
            "brand": brand,
        })

    start = date(2024, 1, 1)
    dates = []
    for offset in range(731):
        d = start + timedelta(days=offset)
        dates.append({
            "date_id": int(d.strftime("%Y%m%d")),
            "year": d.year,
            "quarter": f"Q{((d.month - 1) // 3) + 1}",
            "month": d.month,
            "day": d.day,
        })

    orders = []
    for i in range(1, order_count + 1):
        customer = customers[(i * 17) % len(customers)]
        product = products[(i * 7) % len(products)]
        region = regions[(i * 11) % len(regions)]
        day = dates[(i * 13) % len(dates)]
        quantity = 1 + ((i * 5) % 8)
        base = 29 + ((i * 97) % 9800)
        # Keep amounts varied enough to exercise ranking and aggregation.
        amount = round(base * quantity / 3.0 + rng.random(), 2)
        orders.append({
            "order_id": f"DEMO{i:010d}",
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "date_id": day["date_id"],
            "region_id": region["region_id"],
            "order_quantity": quantity,
            "order_amount": amount,
        })
    return regions, customers, products, dates, orders


async def main() -> None:
    seed = int(os.getenv("DEMO_SEED", "20261104"))
    order_count = int(os.getenv("DEMO_ORDER_COUNT", "10000"))
    product_count = int(os.getenv("DEMO_PRODUCT_COUNT", "50"))
    region_count = int(os.getenv("DEMO_REGION_COUNT", "20"))
    customer_count = int(os.getenv("DEMO_CUSTOMER_COUNT", "200"))
    regions, customers, products, dates, orders = _rows(
        seed, order_count, product_count, region_count, customer_count
    )

    engine = create_async_engine(_db_url(), pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT IGNORE INTO dim_region(region_id, province, region_name, country)
            VALUES (:region_id, :province, :region_name, :country)
        """), regions)
        await conn.execute(text("""
            INSERT IGNORE INTO dim_customer(customer_id, customer_name, gender, member_level)
            VALUES (:customer_id, :customer_name, :gender, :member_level)
        """), customers)
        await conn.execute(text("""
            INSERT IGNORE INTO dim_product(product_id, product_name, category, brand)
            VALUES (:product_id, :product_name, :category, :brand)
        """), products)
        await conn.execute(text("""
            INSERT IGNORE INTO dim_date(date_id, year, quarter, month, day)
            VALUES (:date_id, :year, :quarter, :month, :day)
        """), dates)
        await conn.execute(text("""
            INSERT IGNORE INTO fact_order(order_id, customer_id, product_id, date_id, region_id, order_quantity, order_amount)
            VALUES (:order_id, :customer_id, :product_id, :date_id, :region_id, :order_quantity, :order_amount)
        """), orders)

        print("seeded", {"orders": len(orders), "products": len(products), "regions": len(regions), "customers": len(customers), "dates": len(dates)})
        for table in ("fact_order", "dim_product", "dim_region", "dim_customer", "dim_date"):
            count = (await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar_one()
            print(table, count)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
