# test_api.py - Test if API key is working
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    # Test Gemini import
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        print("✅ Gemini configured successfully")
    except Exception as e:
        print(f"❌ Gemini error: {e}")
else:
    print("❌ No API key found")
    print("Create .env file with: GEMINI_API_KEY=your_key_here")