from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, List

from api.dependencies import get_db
from .models import MenuItemModel, OrderModel

router = APIRouter(prefix="/menu-items", tags=["Menu Management"])

@router.get("/", response_model=List[MenuItemModel])
async def get_all_menu_items(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Returns all active menu items.
    """
    cursor = db["menu_items"].find({"is_active": True})
    items = await cursor.to_list(length=1000)
    return items

@router.patch("/{item_id}")
async def update_menu_item_price(
    item_id: str,
    update_data: Dict[str, float],
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Updates the selling price of a menu item.
    """
    if "selling_price" not in update_data:
        raise HTTPException(status_code=400, detail="Missing selling_price in update data")
        
    new_price = update_data["selling_price"]
    
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID")
        
    result = await db["menu_items"].update_one(
        {"_id": ObjectId(item_id)},
        {"$set": {"selling_price": new_price}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
        
    return {"status": "success", "message": f"Price updated to {new_price}"}


@router.post("/orders", response_model=OrderModel)
async def create_order(order: OrderModel, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Creates a new order and saves it to the database.
    This order will automatically appear on the Kitchen Display System (KDS).
    """
    # Generate a simple order number if not provided
    if not order.orderNumber:
        count = await db["orders"].count_documents({})
        order.orderNumber = f"ORD-{100 + count + 1}"
    
    order_dict = order.model_dump(by_alias=True)
    if "_id" in order_dict and order_dict["_id"] is None:
        del order_dict["_id"]
        
    result = await db["orders"].insert_one(order_dict)
    order.id = result.inserted_id
    return order

