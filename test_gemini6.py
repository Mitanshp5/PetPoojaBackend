import asyncio
import os
import traceback
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_live():
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
    
    config_audio = {
        'response_modalities': ['AUDIO'],
        'system_instruction': types.Content(parts=[types.Part.from_text(text='Hello')])
    }
    try:
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest', config=config_audio) as session:
            print('Connected to 2.5-native with AUDIO modality!')
    except Exception as e:
        print(f"Failed 2.5 native config: {e}")

asyncio.run(test_live())
