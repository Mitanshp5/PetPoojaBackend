from fastapi import FastAPI, Depends
from typing import List
from modules.core_pos.models import OrderModel
from api.dependencies import get_db

app = FastAPI(title="Mobile Ordering Service", description="Handles voice ordering copilot")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Mobile Ordering Service API"}

@app.post("/orders", response_model=OrderModel)
async def place_order(order: OrderModel, db = Depends(get_db)):
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