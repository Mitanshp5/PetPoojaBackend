import asyncio
import os
import traceback
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

async def test_live():
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
    config = {
        'system_instruction': types.Content(parts=[types.Part.from_text(text='Hello')])
    }
    
    # Let's try gemini-2.0-flash-lite-preview-02-05
    try:
        async with client.aio.live.connect(model='gemini-2.0-flash-lite-preview-02-05', config=config) as session:
            print('Connected to flash-lite-preview-02-05')
    except Exception as e:
        print(f"Failed lite-preview: {e}")

    try:
        # Try response modality text for native audio
        config_audio = {
            'system_instruction': types.Content(parts=[types.Part.from_text(text='Hello')]),
        }
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest', config=config_audio) as session:
            print('Connected to 2.5-native with config!')
    except Exception as e:
        print(f"Failed 2.5 native config: {e}")

asyncio.run(test_live())
