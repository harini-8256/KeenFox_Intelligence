import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
    
    # Competitor discovery settings
    DEFAULT_COMPETITORS = ["Notion", "Asana", "ClickUp", "Monday.com", "Microsoft 365 Copilot"]
    
    # Data sources
    SIGNAL_SOURCES = {
        "g2_reviews": True,
        "pricing_pages": True,
        "linkedin": False,  # Requires API key
        "reddit": True,
        "news_articles": True,
        "product_hunt": True,
        "capterra": True
    }
    
    # Scraping settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # AI settings
    MODEL_NAME = "gemini-2.5-flash"  # Updated to available model
    TEMPERATURE = 0.3
    MAX_TOKENS = 8192
    
    # Cache settings
    CACHE_TTL = 3600  # 1 hour
    ENABLE_CACHE = True
    
    # Output settings
    OUTPUT_DIR = "reports"
    SAVE_JSON = True
    SAVE_MARKDOWN = True