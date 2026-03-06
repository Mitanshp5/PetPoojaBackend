import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1alpha/models?key={api_key}'

response = requests.get(url)
data = response.json()

models = [m['name'] for m in data.get('models', []) if 'gemini-2.0' in m.get('name', '')]
print("Models:", models)
