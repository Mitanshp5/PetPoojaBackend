import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'

response = requests.get(url)
data = response.json()

for model in data.get('models', []):
    name = model.get('name', '')
    if 'gemini-2.0' in name:
        print(f"Model: {name}, Actions: {model.get('supportedActions', [])}")
