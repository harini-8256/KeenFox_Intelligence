from typing import List, Dict, Any
from models import CompetitiveSignal, CampaignRecommendation, Priority, IntelligenceReport
from intelligence_engine import IntelligenceAnalyzer
import json

class CampaignStrategyEngine:
    def __init__(self, analyzer: IntelligenceAnalyzer):
        self.analyzer = analyzer
    
    async def generate_messaging_recommendations(self, report: IntelligenceReport) -> List[CampaignRecommendation]:
        """Generate specific messaging and positioning recommendations"""
        
        # Extract key insights
        competitor_weaknesses = []
        for analysis in report.analyses:
            competitor_weaknesses.extend(analysis.weaknesses[:3])
        
        prompt = f"""
        Based on this competitive intelligence report:
        
        Market Insights: {json.dumps(report.market_insights, indent=2)}
        Competitor Weaknesses: {competitor_weaknesses}
        Key Findings: {report.key_findings}
        
        Generate 3 specific messaging recommendations for KeenFox including:
        
        1. Homepage headline recommendation (2 options)
        2. Cold email template for outbound sales
        3. LinkedIn ad copy (3 variations)
        4. Key differentiation points to emphasize in all messaging
        
        For each recommendation, provide:
        - Specific copy/text
        - Rationale based on competitor data
        - Expected impact
        
        Return as JSON array with structure:
        [
            {{
                "channel": "homepage|cold_email|linkedin_ad|general",
                "recommendation": "specific recommendation",
                "copy_examples": ["example1", "example2"],
                "rationale": "why this works based on data",
                "target_audience": "who this is for",
                "a_b_test_suggestions": ["test1", "test2"]
            }}
        ]
        """
        
        response = await self.analyzer.extract_with_gemini(prompt, temperature=0.7)
        
        try:
            recommendations_data = json.loads(response)
            recommendations = []
            
            for rec in recommendations_data:
                campaign_rec = CampaignRecommendation(
                    dimension="messaging",
                    title=f"Messaging for {rec['channel']}",
                    description=rec['recommendation'],
                    rationale=rec['rationale'],
                    priority=Priority.HIGH,
                    implementation_steps=rec.get('a_b_test_suggestions', []),
                    expected_impact="Improved conversion and differentiation",
                    metrics_to_track=["CTR", "Conversion rate", "Time on page"]
                )
                recommendations.append(campaign_rec)
            
            return recommendations
        
        except:
            return []
    
    async def generate_channel_recommendations(self, report: IntelligenceReport) -> List[CampaignRecommendation]:
        """Recommend channel strategy based on competitor activity"""
        
        # Analyze channel presence
        channel_activity = {}
        for analysis in report.analyses:
            for signal in analysis.signals:
                source = signal.source
                if source not in channel_activity:
                    channel_activity[source] = 0
                channel_activity[source] += 1
        
        prompt = f"""
        Based on competitor channel activity:
        {json.dumps(channel_activity, indent=2)}
        
        And market insights: {json.dumps(report.market_insights, indent=2)}
        
        Generate 3 channel strategy recommendations including:
        1. Channels to double down on (with specific tactics)
        2. Channels to pull back from
        3. New channels to test
        
        For each recommendation, include:
        - Channel name
        - Specific tactic
        - Budget allocation suggestion
        - Success metrics
        
        Return as JSON array.
        """
        
        response = await self.analyzer.extract_with_gemini(prompt, temperature=0.6)
        
        try:
            recommendations_data = json.loads(response)
            recommendations = []
            
            for rec in recommendations_data:
                campaign_rec = CampaignRecommendation(
                    dimension="channel",
                    title=rec.get('title', 'Channel Recommendation'),
                    description=rec.get('tactic', ''),
                    rationale=rec.get('rationale', ''),
                    priority=Priority.MEDIUM,
                    implementation_steps=[rec.get('tactic', '')],
                    expected_impact=rec.get('expected_impact', ''),
                    metrics_to_track=rec.get('metrics', [])
                )
                recommendations.append(campaign_rec)
            
            return recommendations
        
        except:
            return []
    
    async def generate_gtm_recommendations(self, report: IntelligenceReport) -> List[CampaignRecommendation]:
        """Generate comprehensive GTM strategy recommendations"""
        
        prompt = f"""
        Synthesize this competitive intelligence into 5 prioritized GTM recommendations:
        
        Market Insights: {json.dumps(report.market_insights, indent=2)}
        Feature Comparison: {json.dumps(report.feature_comparison, indent=2)}
        Sentiment Summary: {json.dumps(report.sentiment_summary, indent=2)}
        
        For each recommendation, provide:
        1. Priority (1-5)
        2. Title
        3. Detailed action plan (3-5 steps)
        4. Rationale tied to specific competitor signals
        5. Expected impact (quantitative if possible)
        6. Timeline (short/medium/long term)
        7. Success metrics
        8. Required resources
        
        Focus on recommendations that directly exploit competitor gaps.
        Return as JSON array.
        """
        
        response = await self.analyzer.extract_with_gemini(prompt, temperature=0.7)
        
        try:
            recommendations_data = json.loads(response)
            recommendations = []
            
            for i, rec in enumerate(recommendations_data[:5]):
                priority_map = {1: Priority.HIGH, 2: Priority.HIGH, 3: Priority.MEDIUM, 4: Priority.MEDIUM, 5: Priority.LOW}
                
                campaign_rec = CampaignRecommendation(
                    dimension="gtm",
                    title=rec.get('title', f'Recommendation {i+1}'),
                    description=rec.get('action_plan', ''),
                    rationale=rec.get('rationale', ''),
                    priority=priority_map.get(i+1, Priority.MEDIUM),
                    implementation_steps=rec.get('action_plan', '').split('.') if isinstance(rec.get('action_plan'), str) else [],
                    expected_impact=rec.get('expected_impact', ''),
                    metrics_to_track=rec.get('success_metrics', [])
                )
                recommendations.append(campaign_rec)
            
            return recommendations
        
        except Exception as e:
            print(f"Error generating GTM recommendations: {e}")
            return []