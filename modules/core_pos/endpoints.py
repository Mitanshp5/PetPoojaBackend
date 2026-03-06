from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict

from api.dependencies import get_db
from .models import MenuItemModel

router = APIRouter(prefix="/menu-items", tags=["Menu Management"])

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
