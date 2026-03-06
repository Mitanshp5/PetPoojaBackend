import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

async def check_schema():
    load_dotenv()
    url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(url)
    db = client["petpooja_db"]
    orders_col = db["orders"]
    
    print("Fetching 5 orders to inspect schema...")
    orders = await orders_col.find({"items": {"$exists": True, "$not": {"$size": 0}}}).limit(5).to_list(length=5)
    
    for i, o in enumerate(orders):
        print(f"\n--- Order {i+1} ({o['_id']}) ---")
        items = o.get("items", [])
        print(f"Total Items: {len(items)}")
        for item in items:
            print(f"  Item keys: {list(item.keys())}")
            print(f"  menu_item_id type: {type(item.get('menu_item_id'))} value: {item.get('menu_item_id')}")
            print(f"  qty: {item.get('qty')} | quantity: {item.get('quantity')}")

if __name__ == "__main__":
    asyncio.run(check_schema())
