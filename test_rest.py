import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'

response = requests.get(url)
data = response.json()

for model in data.get('models', []):
    if 'supportedActions' in model and 'bidiGenerateContent' in model['supportedActions']:
        print(f"BIDI SUPPORTED: {model['name']}")
