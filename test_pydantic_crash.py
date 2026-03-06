import asyncio
import os
import traceback
from google import genai
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

async def test_live():
    # Import the SAME things fastapi imports to reproduce the global state
    from modules.core_pos.models import PyObjectId
    
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
    config = {
        'response_modalities': ['AUDIO'],
        'system_instruction': types.Content(parts=[types.Part.from_text(text='Hello')])
    }
    try:
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest', config=config) as session:
            print('Connected to 2.5-native with config!')
    except Exception as e:
        print(f"Failed 2.5 native config:")
        traceback.print_exc()

asyncio.run(test_live())
