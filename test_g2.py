# test_g2.py
import requests
from bs4 import BeautifulSoup

competitor = "asana"
url = f"https://www.g2.com/products/{competitor}/reviews"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=10)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    # Look for review text
    text = soup.get_text()
    if "review" in text.lower():
        print("✅ G2 page loaded")
    else:
        print("⚠️ Page loaded but no reviews found")
else:
    print(f"❌ G2 blocked. Status: {response.status_code}")