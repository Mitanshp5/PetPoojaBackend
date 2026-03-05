import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import connect_to_mongo, close_mongo_connection, get_database
from modules.core_pos.models import MenuItemModel

async def seed_database():
    print("Connecting to MongoDB...")
    await connect_to_mongo()
    db = get_database()
    
    collection = db["menu_items"]

    # Check if we already have items
    existing_item = await collection.find_one()
    if existing_item:
        print("Database already seeded. Skipping.")
        await close_mongo_connection()
        return

    print("Seeding database...")
    items = [
        MenuItemModel(name="Margherita Pizza", description="Classic cheese and tomato", selling_price=300, food_cost=100, category="Pizza").dict(by_alias=True, exclude={"id"}),
        MenuItemModel(name="Pepperoni Pizza", description="Mozzarella and pepperoni", selling_price=400, food_cost=150, category="Pizza").dict(by_alias=True, exclude={"id"}),
        MenuItemModel(name="Garlic Bread", description="Toasted bread with garlic butter", selling_price=150, food_cost=40, category="Sides").dict(by_alias=True, exclude={"id"}),
        MenuItemModel(name="Coke", description="Cold beverage", selling_price=60, food_cost=20, category="Beverages").dict(by_alias=True, exclude={"id"}),
        MenuItemModel(name="Pasta Alfredo", description="Creamy white sauce pasta", selling_price=350, food_cost=120, category="Pasta").dict(by_alias=True, exclude={"id"}),
    ]

    await collection.insert_many(items)
    print("Database seeded successfully!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(seed_database())
