import hashlib
import json
from datetime import datetime
from typing import Any, Dict

def generate_hash(content: Any) -> str:
    """Generate hash for deduplication"""
    content_str = json.dumps(content, sort_keys=True, default=str)
    return hashlib.md5(content_str.encode()).hexdigest()

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def extract_dates(text: str) -> list:
    """Extract dates from text"""
    import re
    patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}/\d{2}/\d{4}',
        r'[A-Z][a-z]+ \d{1,2}, \d{4}'
    ]
    
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    
    return dates

def chunk_text(text: str, max_length: int = 2000) -> list:
    """Split text into chunks for processing"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_length:
            current_chunk.append(word)
            current_length += len(word) + 1
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks