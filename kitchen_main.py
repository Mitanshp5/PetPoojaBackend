from fastapi import FastAPI, Depends, HTTPException
from typing import List
from modules.core_pos.models import OrderModel
from api.dependencies import get_db
from bson import ObjectId
from pydantic import BaseModel

app = FastAPI(title="Kitchen Service")

class StatusUpdate(BaseModel):
    status: str

@app.get("/orders", response_model=List[OrderModel])
async def get_active_orders(db = Depends(get_db)):
    # Fetch orders that are not completed or cancelled
    orders = await db["orders"].find(
        {"status": {"$in": ["new", "preparing", "ready"]}}
    ).to_list(100)
    return orders

@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, status_update: StatusUpdate, db = Depends(get_db)):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(status_code=400, detail="Invalid order ID")
        
    result = await db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status_update.status}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found or status unchanged")
    return {"message": "Status updated successfully"}