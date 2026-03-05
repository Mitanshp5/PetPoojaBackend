import os
import json
import asyncio
import base64
from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env variables
load_dotenv()

async def handle_gemini_live_session(websocket: WebSocket, menu_context: str):
    """
    Handles a bidirectional WebSocket session between the browser and Gemini Live API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    
    # Define the process_order tool for Gemini to use
    process_order_tool = {
        "function_declarations": [
            {
                "name": "process_order",
                "description": "Updates the customer's digital shopping cart. Call this when the user wants to add, remove, or modify items.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "items": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "action": {"type": "STRING", "description": "add or remove"},
                                    "item_name": {"type": "STRING", "description": "The name of the menu item"},
                                    "quantity": {"type": "INTEGER", "description": "Number of units"},
                                    "notes": {"type": "STRING", "description": "Special instructions like 'spicy' or 'extra cheese'"}
                                },
                                "required": ["action", "item_name", "quantity"]
                            }
                        }
                    },
                    "required": ["items"]
                }
            }
        ]
    }

    config = {
        "tools": [process_order_tool], 
        "system_instruction": f"You are a Voice ordering copilot for PetPooja. ALWAYS use the 'process_order' tool whenever a user mentions ordering something. Use the following menu: {menu_context}."
    }

    
    try:
        async with client.aio.live.connect(model="gemini-2.0-flash-exp", config=config) as session:
            
            async def send_to_gemini():
                try:
                    while True:
                        message = await websocket.receive_json()
                        if "realtime_input" in message:
                            # Frontend sends base64 encoded PCM audio
                            audio_data = message["realtime_input"]["media_chunks"][0]["data"]
                            await session.send(input=audio_data, end_of_turn=False)
                        elif "client_content" in message:
                            # Handle text if needed
                            await session.send(input=message["client_content"]["turns"][0]["parts"][0]["text"], end_of_turn=True)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    print(f"Error in send_to_gemini: {e}")

            async def receive_from_gemini():
                try:
                    async for response in session:
                        if response.server_content and response.server_content.model_turn:
                            parts = response.server_content.model_turn.parts
                            for part in parts:
                                if part.inline_data:
                                    # Send back audio to frontend
                                    await websocket.send_json({
                                        "realtime_output": {
                                            "media_chunks": [{
                                                "mime_type": "audio/pcm;rate=16000",
                                                "data": base64.b64encode(part.inline_data.data).decode('utf-8')
                                            }]
                                        }
                                    })
                                elif part.text:
                                    # Send back text if any
                                    await websocket.send_json({"text": part.text})
                        
                        if response.tool_call:
                            # Handle tool calls (cart updates)
                            for call in response.tool_call.function_calls:
                                # We treat function calls as "cart_updates" to trigger frontend state changes
                                await websocket.send_json({
                                    "type": "cart_update",
                                    "call_id": call.id,
                                    "function": call.name,
                                    "args": call.args
                                })
                except Exception as e:
                    print(f"Error in receive_from_gemini: {e}")

            # Run both tasks concurrently
            await asyncio.gather(send_to_gemini(), receive_from_gemini())

    except Exception as e:
        print(f"Gemini Live Connection Error: {e}")
        await websocket.send_json({"error": str(e)})
