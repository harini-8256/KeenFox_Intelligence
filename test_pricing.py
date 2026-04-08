# test_pricing.py
import asyncio
from data_ingestion import DataIngestor

async def test():
    ingestor = DataIngestor()
    
    print("Testing Pricing Pages...")
    result = await ingestor.fetch_pricing_info("walmart")
    
    if result.get("prices_found"):
        print(f"✅ Pricing WORKING! Found prices: {result['prices_found']}")
    else:
        print(f"❌ Pricing NOT working. Result: {result}")

asyncio.run(test())