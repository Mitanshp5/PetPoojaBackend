import sys
import os
import asyncio
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import connect_to_mongo, close_mongo_connection, get_database
from modules.core_pos.models import MenuItemModel, OrderModel, OrderItemModel

async def seed_database():
    print("Connecting to MongoDB...")
    await connect_to_mongo()
    db = get_database()
    
    items_collection = db["menu_items"]
    orders_collection = db["orders"]

    # Clear existing data for a fresh seed
    print("Clearing existing mock data...")
    await items_collection.delete_many({})
    await orders_collection.delete_many({})

    # 1. Seed Menu Items (Mock Indian Foods)
    # Categorized into High Margin/High Vol, Low Margin/High Vol, etc., to power the Revenue Engine nicely.
    print("Seeding Indian menu items...")
    mock_items = [
        # Breads (High margin, High volume - Stars/Plowhorses)
        MenuItemModel(name="Butter Naan", description="Soft Indian bread brushed with butter", selling_price=60, food_cost=15, category="Bread"),
        MenuItemModel(name="Garlic Naan", description="Naan topped with minced garlic and cilantro", selling_price=75, food_cost=20, category="Bread"),
        MenuItemModel(name="Tandoori Roti", description="Whole wheat bread baked in clay oven", selling_price=40, food_cost=10, category="Bread"),
        
        # Starters/Snacks (Varied)
        MenuItemModel(name="Paneer Tikka", description="Grilled cottage cheese cubes marinated in spices", selling_price=280, food_cost=110, category="Starter"),
        MenuItemModel(name="Samosa (2 pcs)", description="Crispy pastry filled with spiced potatoes", selling_price=80, food_cost=20, category="Starter"),  # High Margin, High Vol
        MenuItemModel(name="Chicken Tikka", description="Tandoor roasted spiced chicken chunks", selling_price=350, food_cost=150, category="Starter"),
        
        # Main Course (Varied Margins)
        MenuItemModel(name="Butter Chicken", description="Chicken simmered in rich tomato gravy", selling_price=450, food_cost=200, category="Main Course"), # Medium Margin, High Vol
        MenuItemModel(name="Dal Makhani", description="Black lentils cooked overnight with butter and cream", selling_price=320, food_cost=80, category="Main Course"), # High Margin, High Vol
        MenuItemModel(name="Palak Paneer", description="Cottage cheese in creamy spinach gravy", selling_price=340, food_cost=140, category="Main Course"),
        MenuItemModel(name="Mutton Rogan Josh", description="Slow cooked lamb in aromatic spices", selling_price=550, food_cost=300, category="Main Course"), # Low Margin, Med Vol
        MenuItemModel(name="Chole Bhature", description="Spiced chickpeas with fried bread", selling_price=220, food_cost=60, category="Main Course"),
        
        # Rice & Biryani
        MenuItemModel(name="Jeera Rice", description="Basmati rice tempered with cumin seeds", selling_price=160, food_cost=40, category="Rice"),
        MenuItemModel(name="Chicken Biryani", description="Fragrant basmati rice layered with spiced chicken", selling_price=400, food_cost=180, category="Rice"),
        MenuItemModel(name="Veg Dum Biryani", description="Slow cooked rice with mixed vegetables", selling_price=300, food_cost=120, category="Rice"),

        # Beverages & Desserts (Usually High Margin)
        MenuItemModel(name="Mango Lassi", description="Sweet yogurt drink blended with mango pulp", selling_price=120, food_cost=35, category="Beverage"),
        MenuItemModel(name="Masala Chai", description="Indian spiced tea", selling_price=50, food_cost=10, category="Beverage"),
        MenuItemModel(name="Gulab Jamun (2 pcs)", description="Deep fried milk dumplings in sugar syrup", selling_price=90, food_cost=25, category="Dessert"),
    ]
    
    # Insert items
    items_data = [item.model_dump(by_alias=True, exclude={"id"}) for item in mock_items]
    result = await items_collection.insert_many(items_data)
    inserted_ids = result.inserted_ids
    
    # Re-fetch to get string IDs easily
    inserted_items = await items_collection.find().to_list(length=100)
    item_map = {item["name"]: str(item["_id"]) for item in inserted_items}

    # 2. Seed Mock Orders (to simulate past data/sales velocity)
    print("Seeding historical orders...")
    mock_orders = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30) # 30 days of mocked data

    # Generate 500 random orders over the last 30 days
    for _ in range(500):
        # Pick 1-4 random items per order
        num_items = random.randint(1, 4)
        order_items_models = []
        total_amount = 0

        # Simulate some logic for combinations (e.g., people who buy Butter Chicken often buy Naan)
        core_meal_item = random.choice(mock_items)
        items_for_this_order = [core_meal_item]
        
        # Hardcode some simple association rules for realistic data
        if core_meal_item.name == "Butter Chicken":
            if random.random() > 0.3: items_for_this_order.append(next(i for i in mock_items if i.name == "Garlic Naan"))
        elif core_meal_item.name == "Dal Makhani":
            if random.random() > 0.4: items_for_this_order.append(next(i for i in mock_items if i.name == "Jeera Rice"))
        elif "Biryani" in core_meal_item.name:
            # Maybe less likely to buy bread with Biryani
            pass
            
        # Add random items to fill up num_items
        while len(items_for_this_order) < num_items:
            items_for_this_order.append(random.choice(mock_items))
            
        # Deduplicate naive approach
        unique_items = list({i.name: i for i in items_for_this_order}.values())

        for item in unique_items:
            qty = random.randint(1, 2)
            total_amount += (item.selling_price * qty)
            order_items_models.append(
                OrderItemModel(menu_item_id=item_map[item.name], quantity=qty).model_dump()
            )

        # Random timestamp within the last 30 days
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        order_time = start_date + timedelta(seconds=random_seconds)

        order_doc = {
            "total_amount": total_amount,
            "status": "completed",
            "source": random.choice(["voice", "manual", "online"]),
            "items": order_items_models,
            "created_at": order_time
        }
        mock_orders.append(order_doc)

    await orders_collection.insert_many(mock_orders)
    
    print(f"Successfully seeded {len(mock_items)} Indian menu items and {len(mock_orders)} historical orders.")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(seed_database())
