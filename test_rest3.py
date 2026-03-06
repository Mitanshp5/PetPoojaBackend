import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1alpha/models?key={api_key}'

response = requests.get(url)
data = response.json()

for model in data.get('models', []):
    name = model.get('name', '')
    actions = model.get('supportedActions', [])
    if 'bidiGenerateContent' in actions:
        print(f"BIDI MODEL: {name}")
