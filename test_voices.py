from google import genai
import traceback
import os
from dotenv import load_dotenv

load_dotenv()
try:
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    # Fetch available models or try random voice names to see if they error
    print("Testing voices...")
except Exception as e:
    traceback.print_exc()
