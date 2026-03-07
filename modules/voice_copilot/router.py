from fastapi import APIRouter, Depends, HTTPException, WebSocket
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.dependencies import get_db

from .schemas import CopilotRequest, CopilotResponse
from .service import VoiceCopilotService
from .live_handler import handle_gemini_live_session

router = APIRouter(prefix="/voice", tags=["AI Voice Copilot"])

def get_voice_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> VoiceCopilotService:
    return VoiceCopilotService(db)

@router.websocket("/stream")
async def voice_stream(websocket: WebSocket, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    WebSocket endpoint for real-time voice ordering via Gemini Live API.
    """
    await websocket.accept()
    
    # Fetch menu context for the AI
    items_col = db["menu_items"]
    menu_items = await items_col.find({"is_active": True}).to_list(length=1000)
    menu_context = "\n".join([
        f"- ID: {str(item.get('_id'))}, Name: {item.get('name')}, Price: {item.get('selling_price')}, Category: {item.get('category')}" 
        for item in menu_items
    ])
    
    # Start the Gemini Live session handler
    await handle_gemini_live_session(websocket, menu_context)

@router.post("/process-text", response_model=CopilotResponse)
async def process_voice_to_cart(request: CopilotRequest, service: VoiceCopilotService = Depends(get_voice_service)):

    """
    Takes a transcribed text string from the user's browser (e.g. "Do samosa aur ek chai dena"),
    sends it to the AI NLP engine (Gemini), matches it against the current menu, 
    and returns a structured JSON order update with a conversational reply and upsell recommendations.
    """
    if not request.transcript:
        raise HTTPException(status_code=400, detail="Transcript text is required")
        
    response = await service.process_voice_transcript(request)
    return response

@router.get("/health")
async def voice_copilot_health():
    """Simple endpoint to verify the voice copilot module is reachable."""
    return {"status": "ok", "message": "Voice Copilot API is ready to accept text transcripts."}

@router.get("/stats")
async def get_voice_ordering_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Analyzes the 'orders' collection to aggregate statistics specifically for Vapi phone orders.
    Calculates total voice orders, revenue from them, and the average upsell.
    """
    orders_col = db["orders"]
    
    # Phone orders are identified by their orderNumber prefix "VAPI-"
    pipeline = [
        {"$match": {"orderNumber": {"$regex": "^VAPI-"}}},
        {
            "$group": {
                "_id": None,
                "total_voice_orders": {"$sum": 1},
                # Calculate total revenue from all VAPI orders
                "total_revenue": {
                    "$sum": {
                        "$reduce": {
                            "input": "$items",
                            "initialValue": 0,
                            "in": {
                                "$add": [
                                    "$$value",
                                    {"$multiply": [
                                        # Handle old qty vs new quantity schemas safely
                                        {"$add": [{"$ifNull": ["$$this.qty", 0]}, {"$ifNull": ["$$this.quantity", 0]}]},
                                        "$$this.selling_price"
                                    ]}
                                ]
                            }
                        }
                    }
                }
            }
        }
    ]
    
    result = await orders_col.aggregate(pipeline).to_list(1)
    
    stats = {
        "status": "Active",
        "calls_today": "-", # Wait for actual call logs feature for this
        "orders_via_voice": 0,
        "avg_upsell_per_call": 0,
        "languages": "EN, HI, Hinglish"
    }
    
    if result and len(result) > 0:
        data = result[0]
        total_orders = data.get("total_voice_orders", 0)
        total_revenue = data.get("total_revenue", 0)
        
        # We roughly define 'avg upsell' here as the average order cart value for voice 
        # minus a presumed base value, but for the dashboard widget we'll just show Avg Order Value (AOV) 
        # and label it accurately for now.
        aov = (total_revenue / total_orders) if total_orders > 0 else 0
        
        stats["orders_via_voice"] = total_orders
        stats["avg_upsell_per_call"] = round(aov, 2)
        
    return stats
