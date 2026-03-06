import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
try:
    models = client.models.list()
    for m in models:
        print(f"Model: {m.name}, Actions: {m.supported_actions}")
except Exception as e:
    print('Failed to list', e)
