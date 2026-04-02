# find_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    genai.configure(api_key=api_key)
    
    print("Available models:\n")
    for model in genai.list_models():
        print(f"Model: {model.name}")
        print(f"  Supported methods: {model.supported_generation_methods}")
        print()
else:
    print("No API key found")