# test_gemini.py - UPDATED with correct model
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print(f"API Key found: {api_key[:15]}...{api_key[-10:] if api_key else 'NOT FOUND'}")
print()

if api_key:
    # Configure Gemini
    genai.configure(api_key=api_key)
    # Use correct model name - gemini-1.5-flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Test with a simple prompt
    print("🔄 Testing Gemini API with gemini-1.5-flash...")
    response = model.generate_content("Say 'Hello from Gemini API!'")
    
    print(f"✅ Gemini Response: {response.text}")
    print()
    print("🎉 Gemini API is working correctly!")
else:
    print("❌ No API key found in .env file")