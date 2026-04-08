import asyncio
import requests

async def test_reddit():
    print("Testing Reddit API...")
    
    url = "https://www.reddit.com/search.json"
    params = {
        'q': 'Asana',
        'limit': 5,
        'sort': 'relevance'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        posts = data.get('data', {}).get('children', [])
        
        print(f"✅ Reddit API WORKING! Found {len(posts)} posts")
        
        for post in posts[:3]:
            post_data = post['data']
            print(f"\n📌 Title: {post_data.get('title', '')[:80]}")
            print(f"   Score: {post_data.get('score', 0)}")
            print(f"   Subreddit: r/{post_data.get('subreddit', '')}")
    else:
        print(f"❌ Reddit API failed. Status: {response.status_code}")

asyncio.run(test_reddit())