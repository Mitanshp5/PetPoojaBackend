import asyncio
import os
import traceback
from google import genai
from dotenv import load_dotenv

load_dotenv()

async def test_live():
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    config = {
        'response_modalities': ['AUDIO'],
        'system_instruction': 'Hello'
    }
    try:
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest', config=config) as session:
            print('Connected. Sending text prompt...')
            await session.send_client_content(turns=[{'role': 'user', 'parts': [{'text': 'Hello, can you hear me?'}]}])
            print('Sent text prompt.')
            async for response in session.receive():
                print(f"Received from Gemini!")
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.text:
                            print(f"Text: {part.text}")
                        elif part.inline_data:
                            print(f"Audio chunk of {len(part.inline_data.data)} bytes")
                break
    except Exception as e:
        print(f"Failed 2.5 native config: {e}")
        traceback.print_exc()

asyncio.run(test_live())
