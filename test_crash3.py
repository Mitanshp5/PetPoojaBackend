import asyncio
import os
import traceback
from google import genai
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

async def test_live():
    # Import main to load EVERYTHING exactly as the server does
    import main
    
    process_order_tool = {
        "function_declarations": [
            {
                "name": "process_order",
                "description": "Updates the customer's digital shopping cart.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "items": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "action": {"type": "STRING"}
                                }
                            }
                        }
                    }
                }
            }
        ]
    }
    
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
    config = {
        'response_modalities': ['AUDIO'],
        'tools': [process_order_tool],
        'system_instruction': types.Content(parts=[types.Part.from_text(text='Hello')])
    }
    try:
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest', config=config) as session:
            print('Connected with tools!')
    except Exception as e:
        print(f"Failed with tools:")
        traceback.print_exc()

asyncio.run(test_live())
