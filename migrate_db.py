import asyncio
import csv
from collections import defaultdict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "petpooja_db")

async def migrate():
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print("Dropping existing collections...")
    await db.menu_items.drop()
    await db.orders.drop()

    print("Loading Menu Items...")
    menu_records = []
    with open("../restaurant_menu_items_2025.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            menu_records.append({
                "item_id_code": row["item_id"],
                "name": row["item_name"],
                "category": row["category"],
                "selling_price": float(row["selling_price"]),
                "food_cost": float(row["food_cost"]),
                "is_active": True
            })
    
    if menu_records:
        await db.menu_items.insert_many(menu_records)
        print(f"Inserted {len(menu_records)} menu items.")

    # Fetch newly inserted items to map their MongoDB ObjectIds
    cursor = db.menu_items.find({})
    name_to_id = {doc["name"]: str(doc["_id"]) async for doc in cursor}

    print("Loading Orders...")
    
    orders_map = defaultdict(list)
    with open("../restaurant_order_items_2025.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orders_map[row["order_id"]].append(row)
            
    order_records = []
    for order_id, items_rows in orders_map.items():
        items = []
        for row in items_rows:
            # Map the exact MongoDB ObjectId
            menu_item_id = name_to_id.get(row["item_name"])
            
            items.append({
                "menu_item_id": menu_item_id,
                "name": row["item_name"],
                "quantity": int(row["quantity"]),
                "modifiers": [],
                "notes": None,
            })
            
        order_records.append({
            "orderNumber": order_id,
            "items": items,
            "created_at": datetime.now(),
            "status": "served", # Historical orders are served
            "type": "dine-in",
            "table": None,
            "time": datetime.now().strftime("%I:%M %p"),
            "elapsed": 0,
            "is_historical": True
        })
        
    if order_records:
        # Insert in chunks to avoid memory/network issues
        chunk_size = 5000
        for i in range(0, len(order_records), chunk_size):
            await db.orders.insert_many(order_records[i:i + chunk_size])
        print(f"Inserted {len(order_records)} historical orders.")

    client.close()
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
