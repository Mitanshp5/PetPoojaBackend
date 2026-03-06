import asyncio
import os
import traceback
from google import genai
from dotenv import load_dotenv

load_dotenv()

async def test_live():
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1alpha'})
    try:
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest') as session:
            print('Connected cleanly without config!')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test_live())
