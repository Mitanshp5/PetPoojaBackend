import os
import json
import asyncio
import base64
from datetime import datetime
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

    # Context-Aware Greeting Logic
    now = datetime.now()
    hour, month = now.hour, now.month
    
    if 12 <= hour < 17: time_greeting = "dopahar"
    elif 17 <= hour < 21: time_greeting = "shaam"
    elif hour >= 21 or hour < 4: time_greeting = "raat"
    else: time_greeting = "subah"
        
    if 3 <= month <= 6: season, suggestion = "garmi", "kuch thanda jaise Lassi ya Ice Cream"
    elif 7 <= month <= 9: season, suggestion = "baarish", "kuch masaledaar jaise Samosa"
    else: season, suggestion = "sardi", "garmagaram soup ya chai"

    instruction_text = (
        f"You are a Voice ordering copilot for PetPooja. ALWAYS use the 'process_order' tool whenever a user mentions ordering something. "
        f"Use the following menu: {menu_context}. "
        f"CONTEXT: It is currently {time_greeting} time during the {season} season. "
        f"YOUR VERY FIRST RESPONSE MUST BE EXACTLY: Namaste! PetPooja mein aapka swagat hai. Iss {season} ki {time_greeting} mein kya aap {suggestion} lena chahenge? "
        f"CRITICAL RULES FOR VOICE OUTPUT: "
        f"1. You MUST speak SLOWLY AND CALMLY. Do NOT generate any preambles, internal thoughts, or process explanations (like 'Formulating the Greeting' or 'Refining the Output'). "
        f"2. You MUST NOT use ANY markdown, asterisks, or brackets in your text. Start directly with the greeting 'Namaste!' "
        f"3. Output ONLY the exact spoken words the customer will hear over the speaker. Never explain your actions."
    )

    config = types.LiveConnectConfig(
        tools=[process_order_tool], 
        system_instruction=types.Content(parts=[types.Part.from_text(text=instruction_text)]),
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"
                )
            )
        )
    )

    try:
        async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-latest", config=config) as session:
            
            # Spark the conversation via text on the backend
            spark_prompt = "Hi. (Remember your system instructions: 0.25x speed, NO markdown or narration, start directly with Namaste!)"
            await session.send_client_content(turns=[{"role": "user", "parts": [{"text": spark_prompt}]}])

            async def send_to_gemini():
                try:
                    while True:
                        message = await websocket.receive_json()
                        if "realtime_input" in message:
                            # Frontend sends base64 encoded PCM audio
                            audio_base64 = message["realtime_input"]["media_chunks"][0]["data"]
                            audio_bytes = base64.b64decode(audio_base64)
                            await session.send_realtime_input(audio={"data": audio_bytes, "mime_type": "audio/pcm;rate=16000"})
                        elif "client_content" in message:
                            # Handle text if needed
                            text = message["client_content"]["turns"][0]["parts"][0]["text"]
                            await session.send_client_content(turns=[{"role": "user", "parts": [{"text": text}]}])
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    print(f"Error in send_to_gemini: {e}")

            async def receive_from_gemini():
                try:
                    async for response in session.receive():
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
        import traceback
        error_trace = traceback.format_exc()
        print(f"Gemini Live Connection Error: {e}")
        with open("gemini_error.log", "w") as f:
            f.write(error_trace)
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
