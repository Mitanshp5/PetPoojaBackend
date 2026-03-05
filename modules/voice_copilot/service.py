import os
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError

from .schemas import CopilotRequest, CopilotResponse, CartItemUpdate
from .nlp_engine import get_gemini_response
from modules.revenue_intelligence.service import RevenueIntelligenceService

class VoiceCopilotService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.items_col = self.db["menu_items"]
        self.revenue_service = RevenueIntelligenceService(db)

    async def process_voice_transcript(self, request: CopilotRequest) -> CopilotResponse:
        """
        Orchestrates taking the user's text transcript, sending it to Gemini for inference,
        and optionally triggering upsell logic from the Revenue Engine.
        """
        # 1. Fetch current active menu to give Gemini context
        menu_items = await self.items_col.find({"is_active": True}).to_list(length=1000)
        
        # 2. Call Gemini API
        try:
           # The nlp_engine handles the raw AI logic
           gemini_output = await get_gemini_response(
               transcript=request.transcript,
               menu_items=menu_items,
               current_cart=request.current_cart
           )
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error calling Gemini: {e}")
            return CopilotResponse(
                reply_text="I'm having trouble connecting to my brain right now. Can you repeat?",
                cart_updates=[],
                intent="error"
            )

        # 3. Parse and Validate the JSON output into our Pydantic schema
        try:
            # We enforce structure through validation
            response = CopilotResponse(**gemini_output)
        except ValidationError as e:
            print(f"Gemini returned invalid schema: {e}")
            return CopilotResponse(
                reply_text="Sorry, I misunderstood the order details. Can you say that again?",
                cart_updates=[],
                intent="error"
            )

        # 4. Integrate with Revenue Engine for Upsells
        # If the user is adding items or requesting checkout, check if we should suggest a combo
        if response.intent in ["add_item", "checkout"] and response.cart_updates:
            # Find combo recommendations based on what's currently in their cart/being added
            combos = await self.revenue_service.get_combo_recommendations(minimum_support=3)
            
            # Simple logic: pick the first recommended item that pairs with something they just ordered
            new_item_ids = [item.menu_item_id for item in response.cart_updates if item.action == "add"]
            
            for recommendation in combos.recommendations:
                if recommendation.primary_item_id in new_item_ids:
                    upsell_item_name = recommendation.recommended_item_name
                    # Make the AI sound natural by appending to its own reply
                    response.reply_text += f" Would you like to add some {upsell_item_name} with that? It's a popular combo."
                    # We just suggest one upsell per turn to not overwhelm
                    break

        return response
