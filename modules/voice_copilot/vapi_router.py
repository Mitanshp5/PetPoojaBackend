from fastapi import APIRouter, Request, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.dependencies import get_db
import json
from datetime import datetime
from modules.core_pos.models import OrderModel, OrderItemModel
from modules.revenue_intelligence.service import RevenueIntelligenceService

router = APIRouter(prefix="/voice/vapi", tags=["Vapi Voice Copilot"])

@router.post("/webhook")
async def vapi_webhook(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Handles Vapi Server Tool Calls.
    Vapi sends a POST request with the following structure:
    {
      "message": {
        "type": "tool-calls",
        "toolWithToolCallList": [
          {
            "tool": { ... },
            "toolCall": {
              "id": "call_abc123",
              "function": {
                "name": "get_menu",
                "arguments": "{}"
              }
            }
          }
        ]
      }
    }
    """
    try:
        payload = await request.json()
        print("--- VAPI WEBHOOK PAYLOAD ---")
        print(json.dumps(payload, indent=2))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    message = payload.get("message", {})
    msg_type = message.get("type")

    # We only care about tool-calls for now
    if msg_type != "tool-calls":
        return {"status": "ignored", "reason": f"Unhandled message type: {msg_type}"}

    tool_call_list = message.get("toolWithToolCallList", [])
    results = []

    for item in tool_call_list:
        tool_call = item.get("toolCall", {})
        call_id = tool_call.get("id")
        function = tool_call.get("function", {})
        name = function.get("name")
        
        args_raw = function.get("arguments", {})
        if isinstance(args_raw, dict):
            args = args_raw
        else:
            try:
                args = json.loads(args_raw)
            except (json.JSONDecodeError, TypeError):
                args = {}

        if name == "get_menu":
            # Fetch active menu items
            menu_items = await db["menu_items"].find({"is_active": True}).to_list(length=1000)
            formatted_menu = []
            for m in menu_items:
                formatted_menu.append({
                    "id": str(m.get("_id", m.get("id"))),
                    "name": m.get("name"),
                    "category": m.get("category"),
                    "price": m.get("selling_price", 0),
                    "description": m.get("description", ""),
                    "veg": m.get("veg", True)
                })
            
            results.append({
                "toolCallId": call_id,
                "result": json.dumps({"menu": formatted_menu})
            })

        elif name == "get_upsell_recommendations":
            # Call the Revenue Intelligence service to get data-driven combo suggestions
            ri_service = RevenueIntelligenceService(db)
            try:
                # Get the top recommended combos (minimum support threshold)
                combos = await ri_service.get_combo_recommendations(minimum_support=3)
                
                # Format the recommendations for the voice assistant
                suggestions = []
                for rec in combos.recommendations:
                    suggestions.append({
                        "if_customer_orders": rec.primary_item_name,
                        "suggest_this_combo": rec.recommended_item_name,
                        "confidence_score": rec.confidence_score
                    })
                
                results.append({
                    "toolCallId": call_id,
                    "result": json.dumps({
                        "message": "Here are the top data-driven combo recommendations based on historical order patterns.",
                        "recommendations": suggestions
                    })
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                results.append({
                    "toolCallId": call_id,
                    "error": f"Failed to fetch upsell recommendations: {e}"
                })

        elif name == "place_order":
            # For headless phone calls, the AI tracks the cart and submits the final list of items.
            items_raw = args.get("items", [])
            
            if not items_raw:
                results.append({
                    "toolCallId": call_id,
                    "error": "No items provided to place order."
                })
                continue

            order_items = []
            
            # Match spoken items to DB objects to get the real ID
            for i in items_raw:
                item_name = i.get("item_name", "")
                qty = i.get("quantity", 1)
                notes = i.get("notes", "")
                modifiers = i.get("modifiers", [])
                
                # Simple exact match or fallback to just using the name if not found.
                db_item = await db["menu_items"].find_one({"name": {"$regex": f"^{item_name}$", "$options": "i"}})
                
                order_items.append(
                    OrderItemModel(
                        menu_item_id=str(db_item["_id"]) if db_item else "voice_custom_item",
                        name=db_item["name"] if db_item else item_name,
                        qty=qty,
                        modifiers=modifiers,
                        notes=notes
                    )
                )

            # Generate order number like VAPI-1234
            short_id = call_id[-4:] if call_id else "0000"
            order_number = f"VAPI-{short_id}"

            new_order = OrderModel(
                orderNumber=order_number,
                items=order_items,
                status="new",
                type="delivery", # Phone orders default to delivery/takeaway
                time=datetime.now().strftime("%I:%M %p")
            )

            # Insert into Kitchen Display collection
            await db["orders"].insert_one(new_order.model_dump(by_alias=True, exclude={"id"}))

            results.append({
                "toolCallId": call_id,
                "result": f"Successfully placed order {order_number} containing {len(order_items)} items into the Kitchen Display!"
            })
        
        else:
            results.append({
                "toolCallId": call_id,
                "error": f"Unknown function {name}. Available functions are get_menu and place_order."
            })

    return {"results": results}
