import asyncio
from data_ingestion import DataIngestor

async def test():
    ingestor = DataIngestor()
    
    print("Testing Reddit fetch...")
    results = await ingestor.fetch_reddit_discussions("Asana")
    
    print(f"✅ Found {len(results)} Reddit posts")
    
    for post in results[:3]:
        print(f"\n📌 {post.get('title', '')[:80]}")
        print(f"   Score: {post.get('score', 0)}")

asyncio.run(test())