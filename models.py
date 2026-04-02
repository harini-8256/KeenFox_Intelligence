from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class SignalType(str, Enum):
    FEATURE_LAUNCH = "feature_launch"
    PRICING_CHANGE = "pricing_change"
    MESSAGING_SHIFT = "messaging_shift"
    CUSTOMER_SENTIMENT = "customer_sentiment"
    GAP_OPPORTUNITY = "gap_opportunity"
    MARKET_TREND = "market_trend"
    COMPETITIVE_THREAT = "competitive_threat"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class CompetitiveSignal:
    competitor: str
    signal_type: SignalType
    title: str
    content: str
    timestamp: datetime
    source: str
    confidence: float
    priority: Priority
    sentiment_score: Optional[float] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class CompetitorAnalysis:
    competitor_name: str
    signals: List[CompetitiveSignal]
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    market_position: str
    last_updated: datetime

@dataclass
class IntelligenceReport:
    report_id: str
    generated_at: datetime
    competitors: List[str]
    analyses: List[CompetitorAnalysis]
    market_insights: Dict[str, Any]
    sentiment_summary: Dict[str, Any]
    feature_comparison: Dict[str, Any]
    key_findings: List[str]
    strategic_recommendations: List[Dict[str, Any]]

@dataclass
class CampaignRecommendation:
    dimension: str  # messaging, channel, gtm
    title: str
    description: str
    rationale: str
    priority: Priority
    implementation_steps: List[str]
    expected_impact: str
    metrics_to_track: List[str]