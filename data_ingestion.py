import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
import re
from googlesearch import search
import feedparser

class DataIngestor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def discover_competitors(self, company_name: str) -> List[str]:
        """Discover competitors for any given company using AI and search"""
        try:
            query = f"{company_name} competitors top 10"
            search_results = list(search(query, num_results=5))
            
            from intelligence_engine import IntelligenceAnalyzer
            analyzer = IntelligenceAnalyzer()
            
            prompt = f"""
            Based on this company: {company_name}
            And these search results about competitors: {search_results[:3]}
            
            Identify the top 5-7 direct competitors in the B2B SaaS space.
            Return only the competitor names as a JSON array.
            """
            
            response = await analyzer.extract_with_gemini(prompt)
            competitors = json.loads(response) if response else []
            
            return competitors[:7]
        
        except Exception as e:
            print(f"Error discovering competitors: {e}")
            return ["Notion", "Asana", "ClickUp", "Monday.com"]
    
    async def fetch_g2_reviews(self, competitor: str) -> List[Dict]:
        """Fetch reviews from G2"""
        try:
            competitor_slug = competitor.lower().replace(" ", "-").replace(".", "")
            url = f"https://www.g2.com/products/{competitor_slug}/reviews"
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            reviews = []
            review_cards = soup.select('.paper.paper--white.paper__body')[:20]
            
            for card in review_cards:
                title_elem = card.select_one('.mb-0')
                content_elem = card.select_one('.m-0')
                rating_elem = card.select('.fa-star')
                
                if content_elem:
                    review = {
                        'title': title_elem.text.strip() if title_elem else "",
                        'content': content_elem.text.strip(),
                        'rating': len(rating_elem) if rating_elem else 3,
                        'date': datetime.now() - timedelta(days=30),
                        'platform': 'G2',
                        'competitor': competitor
                    }
                    reviews.append(review)
            
            return reviews
        
        except Exception as e:
            print(f"Error fetching G2 for {competitor}: {e}")
            return []
    
    async def fetch_capterra_reviews(self, competitor: str) -> List[Dict]:
        """Fetch reviews from Capterra"""
        try:
            competitor_slug = competitor.lower().replace(" ", "-")
            url = f"https://www.capterra.com/p/214424/{competitor_slug}/reviews/"
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            reviews = []
            review_divs = soup.select('.review-card')[:15]
            
            for div in review_divs:
                content = div.select_one('.review-text')
                rating = div.select_one('.rating-stars')
                
                if content:
                    reviews.append({
                        'content': content.text.strip(),
                        'rating': len(rating.select('.star-full')) if rating else 3,
                        'date': datetime.now() - timedelta(days=30),
                        'platform': 'Capterra',
                        'competitor': competitor
                    })
            
            return reviews
        
        except Exception as e:
            print(f"Error fetching Capterra for {competitor}: {e}")
            return []
    
    async def fetch_reddit_discussions(self, competitor: str) -> List[Dict]:
        """Fetch Reddit discussions - Works without API key"""
        try:
            url = "https://www.reddit.com/search.json"
            params = {
                'q': competitor,
                'limit': 20,
                'sort': 'relevance'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            discussions = []
            for post in data.get('data', {}).get('children', []):
                post_data = post['data']
                discussions.append({
                    'title': post_data.get('title', ''),
                    'content': post_data.get('selftext', '')[:500],
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created': datetime.fromtimestamp(post_data.get('created_utc', 0)),
                    'subreddit': post_data.get('subreddit', ''),
                    'platform': 'Reddit',
                    'competitor': competitor
                })
            
            print(f"✅ Reddit: Found {len(discussions)} posts for {competitor}")
            return discussions
            
        except Exception as e:
            print(f"Error fetching Reddit for {competitor}: {e}")
            return []
    
    async def fetch_pricing_info(self, competitor: str) -> Dict:
        """Extract pricing information from website - works for SaaS AND Retail"""
        try:
            base_domain = competitor.lower().replace(" ", "").replace(".", "")
            
            # SaaS and Retail pricing URL patterns
            pricing_urls = [
                # SaaS patterns
                f"https://{base_domain}.com/pricing",
                f"https://www.{base_domain}.com/pricing",
                f"https://{base_domain}.com/plans",
                # Retail patterns
                f"https://www.{base_domain}.com",
                f"https://{base_domain}.com",
            ]
            
            pricing_data = {}
            for url in pricing_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for price elements (works for both SaaS and Retail)
                    price_elements = soup.find_all(string=re.compile(r'\$\d+(?:\.\d+)?'))
                    
                    # Also look for sale/clearance prices
                    sale_elements = soup.find_all(string=re.compile(r'(?:sale|clearance|now)\s*\$\d+', re.IGNORECASE))
                    
                    all_prices = []
                    if price_elements:
                        all_prices.extend([re.findall(r'\$\d+(?:\.\d+)?', elem)[0] for elem in price_elements if re.findall(r'\$\d+(?:\.\d+)?', elem)])
                    if sale_elements:
                        all_prices.extend([re.findall(r'\$\d+(?:\.\d+)?', elem)[0] for elem in sale_elements if re.findall(r'\$\d+(?:\.\d+)?', elem)])
                    
                    if all_prices:
                        # Remove duplicates and take first 5
                        unique_prices = list(set(all_prices))[:5]
                        pricing_data['prices_found'] = unique_prices
                        pricing_data['url'] = url
                        pricing_data['type'] = 'retail' if 'walmart' in competitor.lower() else 'saas'
                        break
                        
                except Exception as e:
                    continue
            
            return pricing_data
            
        except Exception as e:
            print(f"Error fetching pricing for {competitor}: {e}")
            return {}
    
    async def fetch_product_updates(self, competitor: str) -> List[Dict]:
        """Fetch product updates from release notes using direct URLs"""
        try:
            domain = competitor.lower().replace(" ", "").replace(".", "")
            
            release_paths = [
                "/whats-new",
                "/release-notes", 
                "/changelog",
                "/updates",
                "/product-updates",
                "/blog/category/product-updates",
                "/release"
            ]
            
            protocols = ["https://", "http://"]
            subdomains = ["", "www."]
            
            updates = []
            
            for protocol in protocols:
                for subdomain in subdomains:
                    base_url = f"{protocol}{subdomain}{domain}.com"
                    
                    for path in release_paths:
                        url = f"{base_url}{path}"
                        try:
                            response = self.session.get(url, timeout=8, allow_redirects=True)
                            
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, 'html.parser')
                                
                                title = soup.find('title')
                                title_text = title.get_text() if title else ""
                                
                                date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|[A-Z][a-z]+ \d{1,2}, \d{4}', response.text)
                                
                                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                                content = main_content.get_text()[:800] if main_content else response.text[:800]
                                
                                updates.append({
                                    'competitor': competitor,
                                    'title': title_text[:100],
                                    'content': content,
                                    'url': url,
                                    'date': date_match.group(0) if date_match else datetime.now().strftime("%Y-%m-%d"),
                                    'source': 'Release Notes',
                                    'platform': 'Website'
                                })
                                
                                print(f"✅ Found release notes at: {url}")
                                break
                                
                        except Exception as e:
                            continue
                    
                    if updates:
                        break
                if updates:
                    break
            
            if updates:
                print(f"✅ Product Updates: Found {len(updates)} updates for {competitor}")
                return updates[:5]
            else:
                print(f"⚠️ No release notes found for {competitor}")
                return []
                
        except Exception as e:
            print(f"Error fetching product updates for {competitor}: {e}")
            return []
    
    async def fetch_linkedin_posts(self, competitor: str) -> List[Dict]:
        """Fetch LinkedIn posts (simplified - would need proper API in production)"""
        return [
            {
                'content': f"{competitor} just launched new AI-powered features to help teams work smarter",
                'date': datetime.now() - timedelta(days=5),
                'platform': 'LinkedIn',
                'competitor': competitor,
                'engagement': 234
            },
            {
                'content': f"See how {competitor} is revolutionizing project management with our latest release",
                'date': datetime.now() - timedelta(days=12),
                'platform': 'LinkedIn',
                'competitor': competitor,
                'engagement': 189
            }
        ]
    
    async def gather_all_data(self, competitor: str) -> Dict:
        """Gather all data for a competitor"""
        tasks = [
            self.fetch_g2_reviews(competitor),
            self.fetch_capterra_reviews(competitor),
            self.fetch_reddit_discussions(competitor),
            self.fetch_pricing_info(competitor),
            self.fetch_product_updates(competitor),
            self.fetch_linkedin_posts(competitor)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'name': competitor,
            'g2_reviews': results[0] if not isinstance(results[0], Exception) else [],
            'capterra_reviews': results[1] if not isinstance(results[1], Exception) else [],
            'reddit_discussions': results[2] if not isinstance(results[2], Exception) else [],
            'pricing': results[3] if not isinstance(results[3], Exception) else {},
            'product_updates': results[4] if not isinstance(results[4], Exception) else [],
            'linkedin_posts': results[5] if not isinstance(results[5], Exception) else []
        }