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
    try:
        async with client.aio.live.connect(model='gemini-2.0-flash', config=config) as session:
            print('Connected successfully!')
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()

asyncio.run(test_live())
