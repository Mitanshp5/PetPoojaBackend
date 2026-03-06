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
    # Insert order into MongoDB
    new_order = await db["orders"].insert_one(order.model_dump(by_alias=True, exclude={"id"}))
    created_order = await db["orders"].find_one({"_id": new_order.inserted_id})
    return created_order