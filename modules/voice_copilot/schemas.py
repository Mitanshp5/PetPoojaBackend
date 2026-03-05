from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class CopilotRequest(BaseModel):
    transcript: str # The text from the frontend Speech-to-Text
    current_cart: List[Dict[str, Any]] = [] # Optional: what they already have in the cart

class CartItemUpdate(BaseModel):
    action: str # "add", "remove", "update_qty"
    menu_item_id: str
    name: str # The human-readable name determined by AI
    quantity: int
    notes: Optional[str] = None # e.g. "make it spicy"

class CopilotResponse(BaseModel):
    reply_text: str # What the AI actually SAYS back to the user (e.g. "Got it, 2 samosas. Want some tea?")
    cart_updates: List[CartItemUpdate] = [] # The structured JSON of what to change in the POS cart
    intent: str # e.g. "adding_item", "checkout", "clarification"
