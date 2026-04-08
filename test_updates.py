# test_updates.py
import asyncio
from data_ingestion import DataIngestor

async def test():
    ingestor = DataIngestor()
    
    print("Testing Product Updates...")
    results = await ingestor.fetch_product_updates("walmart")
    
    if results:
        print(f"✅ Product Updates WORKING! Found {len(results)} updates")
    else:
        print(f"❌ Product Updates NOT working")

asyncio.run(test())