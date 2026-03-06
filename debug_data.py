import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def debug_data():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME")]

    # Check menu items
    menu_count = await db.menu_items.count_documents({})
    print(f"Total Menu Items: {menu_count}")
    
    # Check orders
    order_count = await db.orders.count_documents({})
    print(f"Total Orders: {order_count}")
    
    # Check linked items in orders
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {
            "_id": None,
            "total_items": {"$sum": 1},
            "missing_id": {"$sum": {"$cond": [{"$eq": ["$items.menu_item_id", None]}, 1, 0]}}
        }}
    ]
    linked_stats = await db.orders.aggregate(pipeline).to_list(length=1)
    if linked_stats:
        print(f"Total line items in orders: {linked_stats[0]['total_items']}")
        print(f"Items with MISSING menu_item_id: {linked_stats[0]['missing_id']}")
    else:
        print("No order items found.")

    # Check pair frequency
    orders = await db.orders.find({"items": {"$exists": True}}).to_list(length=100)
    for order in orders:
        ids = [i.get("menu_item_id") for i in order.get("items", [])]
        if len(ids) > 1:
            print(f"Sample order with multiple items: {ids}")
            break

    client.close()

if __name__ == "__main__":
    asyncio.run(debug_data())
