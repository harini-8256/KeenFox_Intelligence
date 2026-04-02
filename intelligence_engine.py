import google.generativeai as genai
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from models import CompetitiveSignal, SignalType, Priority, CompetitorAnalysis
from config import Config
import asyncio

class IntelligenceAnalyzer:
    def __init__(self, api_key: str = None):
        api_key = api_key or Config.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(Config.MODEL_NAME)
        self.conversation_history = {}
    
    async def extract_with_gemini(self, prompt: str, temperature: float = None) -> str:
        """Extract information using Gemini with error handling"""
        try:
            temp = temperature or Config.TEMPERATURE
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt, generation_config={
                    "temperature": temp,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": Config.MAX_TOKENS
                })
            )
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return ""
    
    async def analyze_review_sentiment(self, review: Dict) -> Dict:
        """Deep sentiment analysis of individual reviews"""
        prompt = f"""
        Analyze this customer review for {review.get('competitor', 'unknown')}:
        
        Review: {review.get('content', '')[:1000]}
        Rating: {review.get('rating', 0)}/5
        
        Extract structured insights as JSON:
        {{
            "sentiment": "positive|negative|mixed|neutral",
            "score": float 0-1,
            "key_pain_points": ["pain point 1", "pain point 2"],
            "key_likes": ["like 1", "like 2"],
            "feature_requests": ["feature 1", "feature 2"],
            "competitor_comparisons": ["comparison 1"],
            "use_case": "what they use the product for",
            "team_size": "estimated team size",
            "urgency": "high|medium|low"
        }}
        
        Be specific and actionable.
        """
        
        response = await self.extract_with_gemini(prompt, temperature=0.2)
        try:
            return json.loads(response)
        except:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "key_pain_points": [],
                "key_likes": [],
                "feature_requests": [],
                "competitor_comparisons": [],
                "use_case": "unknown",
                "team_size": "unknown",
                "urgency": "medium"
            }
    
    async def extract_competitive_signals(self, competitor_data: Dict) -> List[CompetitiveSignal]:
        """Extract strategic signals from competitor data"""
        
        # Prepare context
        reviews_summary = []
        for review in competitor_data.get('g2_reviews', [])[:10]:
            sentiment = await self.analyze_review_sentiment(review)
            reviews_summary.append({
                'content': review['content'][:200],
                'sentiment': sentiment
            })
        
        prompt = f"""
        You are a strategic analyst for KeenFox, a B2B SaaS productivity platform.
        
        Analyze this competitor data for {competitor_data['name']}:
        
        Reviews Summary: {json.dumps(reviews_summary, indent=2)}
        Pricing: {competitor_data.get('pricing', {})}
        Product Updates: {competitor_data.get('product_updates', [])[:5]}
        Reddit Discussions: {competitor_data.get('reddit_discussions', [])[:5]}
        LinkedIn Posts: {competitor_data.get('linkedin_posts', [])[:3]}
        
        Extract 8-12 strategic signals. Focus on:
        1. Feature launches that could threaten KeenFox
        2. Pricing changes or packaging moves
        3. Messaging shifts (how they position themselves)
        4. Customer complaints that reveal gaps/opportunities
        5. What customers love (benchmark for KeenFox)
        
        Return as JSON array:
        [
            {{
                "title": "Short, clear title",
                "signal_type": "feature_launch|pricing_change|messaging_shift|customer_sentiment|gap_opportunity|market_trend|competitive_threat",
                "content": "Detailed description of what's happening",
                "confidence": 0.0-1.0,
                "priority": "high|medium|low",
                "strategic_implication": "What KeenFox should do about this",
                "tags": ["tag1", "tag2"]
            }}
        ]
        
        Make each signal actionable and non-obvious.
        """
        
        response = await self.extract_with_gemini(prompt, temperature=0.3)
        
        try:
            # Clean response if it contains markdown
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1]
            
            signals_data = json.loads(response)
            signals = []
            
            for sig in signals_data:
                signal = CompetitiveSignal(
                    competitor=competitor_data['name'],
                    signal_type=SignalType(sig['signal_type']),
                    title=sig['title'],
                    content=sig['content'],
                    timestamp=datetime.now(),
                    source="ai_extraction",
                    confidence=sig['confidence'],
                    priority=Priority(sig['priority']),
                    tags=sig.get('tags', []),
                    metadata={"strategic_implication": sig['strategic_implication']}
                )
                signals.append(signal)
            
            return signals
        
        except Exception as e:
            print(f"Error parsing signals for {competitor_data['name']}: {e}")
            print(f"Response was: {response[:500]}")
            return []
    
    async def generate_market_insights(self, all_signals: List[CompetitiveSignal]) -> Dict:
        """Generate high-level market insights from all signals"""
        
        signals_summary = []
        for signal in all_signals:
            signals_summary.append({
                'competitor': signal.competitor,
                'type': signal.signal_type.value,
                'title': signal.title,
                'priority': signal.priority.value,
                'implication': signal.metadata.get('strategic_implication', '')
            })
        
        prompt = f"""
        Based on these {len(all_signals)} competitive signals from the B2B SaaS productivity market:
        {json.dumps(signals_summary[:20], indent=2)}
        
        Generate strategic market insights for KeenFox:
        
        1. What are the 3 biggest threats in the market right now?
        2. What are the 3 biggest opportunities?
        3. What messaging themes are competitors converging on?
        4. Where are the white spaces/gaps KeenFox can own?
        5. What features are becoming table stakes?
        6. What's the overall market sentiment trend?
        
        Return as JSON with these exact keys:
        {{
            "threats": [{"threat": "description", "severity": "high|medium|low", "affected_competitors": []}],
            "opportunities": [{"opportunity": "description", "potential_impact": "high|medium|low"}],
            "messaging_themes": ["theme1", "theme2"],
            "white_spaces": ["gap1", "gap2"],
            "table_stakes_features": ["feature1", "feature2"],
            "market_sentiment": "bullish|bearish|neutral",
            "key_takeaways": ["takeaway1", "takeaway2"]
        }}
        """
        
        response = await self.extract_with_gemini(prompt, temperature=0.4)
        
        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            return json.loads(response)
        except:
            return {
                "threats": [],
                "opportunities": [],
                "messaging_themes": [],
                "white_spaces": [],
                "table_stakes_features": [],
                "market_sentiment": "neutral",
                "key_takeaways": ["Unable to generate insights"]
            }
    
    async def analyze_competitor(self, competitor_data: Dict) -> CompetitorAnalysis:
        """Complete analysis of a single competitor"""
        
        # Extract signals
        signals = await self.extract_competitive_signals(competitor_data)
        
        # Generate SWOT based on signals
        prompt = f"""
        Based on these signals for {competitor_data['name']}:
        {json.dumps([s.__dict__ for s in signals[:10]], indent=2, default=str)}
        
        Generate SWOT analysis as JSON:
        {{
            "strengths": ["strength1", "strength2", "strength3"],
            "weaknesses": ["weakness1", "weakness2", "weakness3"],
            "opportunities": ["opportunity1", "opportunity2"],
            "threats": ["threat1", "threat2"],
            "market_position": "market leader|challenger|niche player|new entrant"
        }}
        """
        
        response = await self.extract_with_gemini(prompt, temperature=0.3)
        
        try:
            swot = json.loads(response)
        except:
            swot = {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
                "market_position": "unknown"
            }
        
        return CompetitorAnalysis(
            competitor_name=competitor_data['name'],
            signals=signals,
            strengths=swot.get('strengths', []),
            weaknesses=swot.get('weaknesses', []),
            opportunities=swot.get('opportunities', []),
            threats=swot.get('threats', []),
            market_position=swot.get('market_position', 'unknown'),
            last_updated=datetime.now()
        )