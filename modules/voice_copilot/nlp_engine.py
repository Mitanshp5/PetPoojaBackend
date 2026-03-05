import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List

from pydantic import BaseModel, Field
from typing import Optional

class CopilotCartUpdate(BaseModel):
    action: str = Field(description="add or remove")
    menu_item_id: str
    name: str = Field(description="The name of the item from the menu")
    quantity: int
    notes: Optional[str] = Field(None, description="Any special instructions")

class CopilotAIResponse(BaseModel):
    reply_text: str = Field(description="Your conversational response in the user's language/Hinglish.")
    intent: str = Field(description="One of: add_item, remove_item, checkout, clarify, general_query")
    cart_updates: List[CopilotCartUpdate]

async def get_gemini_response(transcript: str, menu_items: List[dict], current_cart: List[dict] = []) -> dict:
    # Load env variables explicitly
    load_dotenv()
    
    # Configure Gemini with the API key from environment
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") 
        
    if not api_key:
        print("CRIT: No API Key found in environment variables!")
        raise ValueError("GEMINI_API_KEY is not set in environment.")

    try:
        # Initialize the modern google-genai client
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"GenAI Auth Error: {e}")
        raise e

    menu_context = "\n".join([
        f"- ID: {item.get('_id')}, Name: {item.get('name')}, Price: {item.get('selling_price')}" 
        for item in menu_items
    ])
    
    cart_context = json.dumps(current_cart) if current_cart else "Empty"

    prompt = f"""
You are an intelligent Voice Ordering Copilot for an Indian restaurant named PetPooja.
You receive a text transcript (often in Hindi or Hinglish) of what the customer said.

CURRENT MENU:
{menu_context}

CURRENT CART:
{cart_context}

CUSTOMER TRANSCRIPT: "{transcript}"

Analyze the transcript. You must reply strictly answering the fields requested. Ensure the reply_text is conversational, and accurately infers intent. If a user asks for "2 samosas", your quantity should be 2. Do NOT hallucinate menu_item_ids, pick them exactly from the list provided.
"""

    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CopilotAIResponse
            )
        )
        # response.text is guaranteed to be a JSON string mapped to CopilotAIResponse
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Failed to call Gemini or parse response: {e}")
        return {
            "reply_text": "Sorry, I had trouble processing that. Could you repeat?",
            "intent": "error",
            "cart_updates": []
        }
    
