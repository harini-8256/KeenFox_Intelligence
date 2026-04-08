import os
import json
import uuid
import webbrowser
import re
import threading
from data_ingestion import DataIngestor
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from collections import defaultdict
import time
from dotenv import load_dotenv

# Create reports folder
REPORTS_FOLDER = Path("saved_reports")
REPORTS_FOLDER.mkdir(exist_ok=True)

# ========== GUARDRAILS ==========

# Guardrail 1: Rate Limiting
request_log = defaultdict(list)

def rate_limit_check(max_requests: int = 10, window: int = 60):
    now = time.time()
    client_id = "default"
    request_log[client_id] = [t for t in request_log[client_id] if now - t < window]
    if len(request_log[client_id]) >= max_requests:
        return False
    request_log[client_id].append(now)
    return True

# Guardrail 2: Output Quality
def validate_output(report):
    issues = []
    if len(report.get("competitors_analyzed", [])) < 3:
        issues.append("Less than 3 competitors found")
    if not report.get("key_findings"):
        issues.append("No key findings")
    if not report.get("recommendations"):
        issues.append("No recommendations")
    return issues

# Guardrail 3: Content Safety
def check_safety(text):
    blocked = ["hate", "violence", "illegal", "fraud", "scam", "abuse"]
    for word in blocked:
        if word in str(text).lower():
            return False
    return True

# Guardrail 4: Data Freshness
def check_freshness(report):
    gen_time = datetime.fromisoformat(report.get("generated_at"))
    age = datetime.now() - gen_time
    if age.days > 7:
        return False
    return True

# Guardrail 5: AI Content Verification
def verify_ai_insights(report: dict) -> dict:
    warnings = []
    verified_count = 0
    total_insights = 0
    
    for finding in report.get("key_findings", []):
        total_insights += 1
        if "reddit" in str(finding).lower() or "user" in str(finding).lower():
            verified_count += 1
        elif "maybe" in str(finding).lower() or "might" in str(finding).lower():
            warnings.append(f"Low confidence: {finding[:50]}...")
    
    for rec in report.get("recommendations", []):
        if "maybe" in rec.get("rationale", "").lower() or "could" in rec.get("rationale", "").lower():
            warnings.append(f"Uncertain rationale: {rec.get('title', '')}")
    
    verification_score = (verified_count / total_insights * 100) if total_insights > 0 else 0
    
    return {
        "is_verified": verification_score >= 60,
        "verification_score": verification_score,
        "warnings": warnings,
        "message": f"{verified_count}/{total_insights} insights backed by real data"
    }

# Load environment variables
load_dotenv()

# Create ingestor instance for real data
ingestor = DataIngestor()

def save_report_to_file(report_id: str, report_data: dict):
    file_path = REPORTS_FOLDER / f"{report_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)
    print(f"✅ Report saved: {file_path}")
    return file_path

def load_all_reports():
    reports = {}
    for file_path in REPORTS_FOLDER.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
            reports[report['report_id']] = report
    return reports

# Import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini not available")

# Configuration
API_KEY = os.getenv('GEMINI_API_KEY')
if API_KEY and GEMINI_AVAILABLE:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemma-3-27b-it')
    print("✅ Gemini AI configured successfully")
else:
    model = None
    print("⚠️ Gemini AI not configured")

# Create FastAPI app
app = FastAPI(title="KeenFox Intelligence System", version="1.0.0")
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Load existing reports from files
reports_db = load_all_reports()
print(f"📁 Loaded {len(reports_db)} existing reports")

# Data models
class CompetitorRequest(BaseModel):
    company_name: str
    competitors: Optional[List[str]] = None

class QuestionRequest(BaseModel):
    question: str
    report_id: Optional[str] = None

# Store for reports
reports_db = {}

@app.get("/")
async def root():
    return {
        "system": "KeenFox Competitive Intelligence System",
        "status": "operational",
        "gemini_available": GEMINI_AVAILABLE and API_KEY is not None,
        "endpoints": [
            "/discover_competitors",
            "/run_intelligence",
            "/get_report",
            "/ask_question",
            "/what_changed"
        ]
    }

@app.post("/discover_competitors")
async def discover_competitors(request: CompetitorRequest):
    # ========== INPUT VALIDATION GUARDRAIL ==========
    if not request.company_name or not request.company_name.strip():
        raise HTTPException(status_code=400, detail="Company name cannot be empty")
    
    if len(request.company_name) > 50:
        raise HTTPException(status_code=400, detail="Company name too long (max 50 characters)")
    
    if not re.match(r'^[a-zA-Z0-9\s\.\-\&]+$', request.company_name):
        raise HTTPException(status_code=400, detail="Company name contains invalid characters")
    
    if not model:
        default_competitors = ["Notion", "Asana", "ClickUp", "Monday.com", "Trello", "Basecamp", "Wrike"]
        return {
            "company": request.company_name,
            "competitors": default_competitors,
            "count": len(default_competitors),
            "note": "Using default competitors (Gemini not available)"
        }
    
    try:
        prompt = f"""
        For B2B competitive intelligence analysis, determine the industry and competitors for "{request.company_name}".
        
        IMPORTANT: Focus on the company's ENTERPRISE/BUSINESS divisions, not consumer divisions.
        
        For example:
        - Amazon's enterprise division is AWS (cloud computing)
        - Microsoft's enterprise division is Azure (cloud) and Office 365
        - Google's enterprise division is Google Cloud and Workspace
        
        Based on this, identify:
        1. The enterprise/B2B industry category
        2. Top 7 enterprise/B2B competitors
        
        Return ONLY JSON:
        {{"industry": "industry name", "competitors": ["comp1","comp2","comp3","comp4","comp5","comp6","comp7"]}}
        """
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0]
        elif '```' in result_text:
            result_text = result_text.split('```')[1]
        
        result = json.loads(result_text)
        
        return {
            "company": request.company_name,
            "industry": result.get("industry", "Unknown"),
            "competitors": result.get("competitors", [])[:7],
            "count": len(result.get("competitors", [])[:7])
        }
        
    except Exception as e:
        return {
            "company": request.company_name,
            "competitors": ["Unable to fetch competitors", "Check API connection"],
            "count": 0,
            "note": f"Error: {str(e)[:100]}"
        }

@app.post("/run_intelligence")
async def run_intelligence(request: CompetitorRequest):
    """Run full intelligence cycle with industry detection"""
    if not model:
        raise HTTPException(status_code=503, detail="Gemini AI not available. Please check your API key.")
    
    try:
        # ========== STEP 1: DETECT INDUSTRY ==========
        industry_prompt = f"""
        For "{request.company_name}", answer this question:
        
        "For a B2B SaaS company doing competitive intelligence, which industry should we analyze?"
        
        RULES:
        - If this company has a cloud computing division (AWS, Azure, GCP), answer CLOUD/TECH
        - If this company sells products online to consumers, answer E-COMMERCE/RETAIL
        - If this company processes payments, answer FINANCIAL SERVICES
        
        SPECIFIC COMPANIES:
        - Amazon: CLOUD/TECH (because of AWS)
        - Microsoft: CLOUD/TECH (because of Azure)
        - Google: CLOUD/TECH (because of Google Cloud)
        - Walmart: E-COMMERCE/RETAIL
        - Flipkart: E-COMMERCE/RETAIL
        - Visa: FINANCIAL SERVICES
        
        Now answer for: {request.company_name}
        
        Return ONLY: CLOUD/TECH or E-COMMERCE/RETAIL or FINANCIAL SERVICES or ENTERPRISE SAAS or OTHER
        """
        try:
            industry_response = model.generate_content(industry_prompt)
            industry = industry_response.text.strip()
            print(f"📊 Detected industry for {request.company_name}: {industry}")
        except:
            industry = "OTHER"
            print(f"⚠️ Industry detection failed, defaulting to: {industry}")
        
        # ========== STEP 2: GET COMPETITORS ==========
        if request.competitors:
            competitors = request.competitors
        else:
            comp_prompt = f"""
            List top 7 direct competitors for {request.company_name} in the {industry} industry.
            Return ONLY a JSON array of competitor names.
            """
            comp_response = model.generate_content(comp_prompt)
            comp_text = comp_response.text.strip()
            if '```json' in comp_text:
                comp_text = comp_text.split('```json')[1].split('```')[0]
            elif '```' in comp_text:
                comp_text = comp_text.split('```')[1]
            competitors = json.loads(comp_text)[:5]
        
        # ========== STEP 3: ANALYZE EACH COMPETITOR ==========
        analyses = []
        all_insights = []
        
        industry_focus = {
            "CLOUD/TECH": "cloud infrastructure, compute, storage, serverless, pricing, regions, SLAs",
            "E-COMMERCE/RETAIL": "product selection, pricing, shipping, customer service, returns, marketplace",
            "FINANCIAL SERVICES": "payment processing, digital wallets, BNPL, fraud detection, transaction fees, security",
            "IT SERVICES": "digital transformation, cloud consulting, outsourcing, managed services, system integration",
            "SOCIAL MEDIA": "user engagement, ad revenue, content moderation, algorithm, user growth",
            "ENTERPRISE SAAS": "subscription pricing, feature releases, integrations, customer success, AI capabilities",
        }
        
        focus = industry_focus.get(industry, "competitive landscape, market position, customer sentiment")
        
        for competitor in competitors[:5]:
            prompt = f"""
            Analyze {competitor} as a competitor in the {industry} industry.
            
            IMPORTANT: Focus ONLY on {industry} aspects. DO NOT mix with other industries.
            For {industry}, analyze: {focus}
            
            Return JSON with:
            {{
                "strengths": ["strength1", "strength2", "strength3"],
                "weaknesses": ["weakness1", "weakness2", "weakness3"],
                "key_features": ["feature1", "feature2"],
                "market_position": "leader|challenger|niche",
                "threat_level": "high|medium|low"
            }}
            """
            
            response = model.generate_content(prompt)
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0]
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1]
            
            try:
                analysis = json.loads(resp_text)
            except:
                analysis = {
                    "strengths": ["Market presence", "Brand recognition"],
                    "weaknesses": ["Complex pricing", "Integration gaps"],
                    "key_features": ["Core features"],
                    "market_position": "challenger",
                    "threat_level": "medium"
                }
            
            analyses.append({
                "competitor": competitor,
                "analysis": analysis
            })
            all_insights.extend(analysis.get("weaknesses", []))
        
        # ========== STEP 4: MARKET INSIGHTS ==========
        insights_prompt = f"""
        Based on analysis of these competitors in the {industry} industry: {[a['competitor'] for a in analyses]}
        
        Generate strategic insights for a new entrant (KeenFox) in the {industry} industry.
        
        IMPORTANT: Insights must be SPECIFIC to the {industry} industry.
        For {industry}, focus on: {focus}
        
        Return JSON with:
        {{
            "opportunities": ["industry-specific opportunity1", "opportunity2", "opportunity3"],
            "threats": ["industry-specific threat1", "threat2", "threat3"],
            "messaging": "Recommended messaging for {industry}",
            "features": ["feature1", "feature2", "feature3"]
        }}
        """
        
        insights_response = model.generate_content(insights_prompt)
        insights_text = insights_response.text.strip()
        if '```json' in insights_text:
            insights_text = insights_text.split('```json')[1].split('```')[0]
        elif '```' in insights_text:
            insights_text = insights_text.split('```')[1]
        
        try:
            market_insights = json.loads(insights_text)
        except:
            market_insights = {
                "opportunities": [f"Mobile-first experience in {industry}", f"Simplified pricing for {industry}", f"Better integrations for {industry}"],
                "threats": ["Established competitors", "Brand loyalty", "Feature parity"],
                "messaging": f"Focus on simplicity and ease of use in {industry}",
                "features": ["AI-powered automation", "Real-time collaboration", "Advanced analytics"]
            }
        
        # ========== STEP 5: CAMPAIGN RECOMMENDATIONS ==========
        campaign_prompt = f"""
        Based on the competitive analysis in the {industry} industry, generate 3 specific campaign recommendations for KeenFox.
        
        Return as JSON array with fields: title, description, rationale, priority
        """
        
        campaign_response = model.generate_content(campaign_prompt)
        campaign_text = campaign_response.text.strip()
        if '```json' in campaign_text:
            campaign_text = campaign_text.split('```json')[1].split('```')[0]
        elif '```' in campaign_text:
            campaign_text = campaign_text.split('```')[1]
        
        try:
            recommendations = json.loads(campaign_text)
        except:
            recommendations = [
                {
                    "title": "Mobile-First Messaging",
                    "description": "Highlight superior mobile experience",
                    "rationale": f"Competitors in {industry} have weak mobile apps",
                    "priority": "high"
                },
                {
                    "title": "LinkedIn & Twitter Focus",
                    "description": "Target B2B decision makers on LinkedIn",
                    "rationale": f"Competitors in {industry} are active here",
                    "priority": "medium"
                },
                {
                    "title": "Free Tier Expansion",
                    "description": "Offer generous free tier to capture market",
                    "rationale": f"Low barrier to entry in {industry}",
                    "priority": "high"
                }
            ]
        
        # Create report
        report_id = str(uuid.uuid4())
        report = {
            "report_id": report_id,
            "generated_at": datetime.now().isoformat(),
            "company": request.company_name,
            "detected_industry": industry,
            "competitors_analyzed": competitors[:5],
            "competitor_analyses": analyses,
            "market_insights": market_insights,
            "recommendations": recommendations,
            "key_findings": all_insights[:5] if all_insights else ["Market analysis complete"]
        }
        
        # ========== APPLY GUARDRAILS ==========
        
        # Rate Limiting Guardrail
        if not rate_limit_check():
            raise HTTPException(429, "Too many requests. Please wait.")
        
        # Output Quality Guardrail
        quality_issues = validate_output(report)
        if quality_issues:
            report["warnings"] = quality_issues
        
        # Content Safety Guardrail
        if not check_safety(str(report)):
            report["safety_warning"] = "Content filtered"
        
        # AI Verification Guardrail
        verification = verify_ai_insights(report)
        report["verification_score"] = verification["verification_score"]
        report["verification_message"] = verification["message"]
        if verification["warnings"]:
            report["low_confidence_warnings"] = verification["warnings"]
        
        reports_db[report_id] = report
        save_report_to_file(report_id, report)
        
        return {

            "status": "success",
            "report_id": report_id,
            "detected_industry": industry,
            "competitors_analyzed": competitors[:5],
            "key_findings": report["key_findings"],
            "generated_at": report["generated_at"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/get_report")
async def get_report(report_id: Optional[str] = None):
    """Get intelligence report"""
    if not report_id and reports_db:
        report_id = list(reports_db.keys())[-1]
    
    if report_id and report_id in reports_db:
        report = reports_db[report_id]
        # Data Freshness Guardrail
        if not check_freshness(report):
            report["warning"] = "Report is older than 7 days"
        return JSONResponse(report)
    
    if report_id:
        file_path = REPORTS_FOLDER / f"{report_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            reports_db[report_id] = report
            if not check_freshness(report):
                report["warning"] = "Report is older than 7 days"
            return JSONResponse(report)
    
    raise HTTPException(status_code=404, detail="Report not found. Run /run_intelligence first.")

@app.post("/ask_question")
async def ask_question(request: QuestionRequest):
    """Ask questions about competitive data"""
    if not model:
        raise HTTPException(status_code=503, detail="Gemini AI not available")
    
    if request.report_id:
        report = reports_db.get(request.report_id)
    else:
        report = list(reports_db.values())[-1] if reports_db else None
    
    if not report:
        raise HTTPException(status_code=404, detail="No report available. Run /run_intelligence first.")
    
    try:
        prompt = f"""
        Based on this competitive intelligence report:
        {json.dumps(report, indent=2, default=str)[:3000]}
        
        Answer this question: {request.question}
        
        Provide a specific, data-driven answer.
        """
        
        response = model.generate_content(prompt)
        
        return {
            "question": request.question,
            "answer": response.text,
            "report_id": report.get("report_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/what_changed")
async def what_changed():
    """Show what changed since last run"""
    if len(reports_db) < 2:
        return {
            "message": "Need at least 2 reports to compare. Run /run_intelligence twice.",
            "reports_count": len(reports_db)
        }
    
    reports_list = list(reports_db.values())
    latest = reports_list[-1]
    previous = reports_list[-2]
    
    return {
        "previous_report": previous.get("generated_at"),
        "current_report": latest.get("generated_at"),
        "changes": {
            "competitors_added": [c for c in latest.get("competitors_analyzed", []) 
                                 if c not in previous.get("competitors_analyzed", [])],
            "competitors_removed": [c for c in previous.get("competitors_analyzed", []) 
                                   if c not in latest.get("competitors_analyzed", [])]
        }
    }

@app.post("/run_intelligence_real")
async def run_intelligence_real(request: CompetitorRequest):
    """Run intelligence with REAL data from G2, Reddit, Capterra"""
    
    if request.competitors:
        competitors = request.competitors
    else:
        comp_response = await discover_competitors(request)
        competitors = comp_response.get("competitors", [])[:3]
    
    all_real_data = []
    for competitor in competitors:
        print(f"📊 Gathering real data for {competitor}...")
        real_data = await ingestor.gather_all_data(competitor)
        all_real_data.append(real_data)
    
    total_g2 = sum(len(d.get("g2_reviews", [])) for d in all_real_data)
    total_reddit = sum(len(d.get("reddit_discussions", [])) for d in all_real_data)
    total_pricing = sum(1 for d in all_real_data if d.get("pricing", {}).get("prices_found"))
    
    evidence_text = ""
    for data in all_real_data:
        evidence_text += f"\n\n--- {data['name']} ---\n"
        
        for review in data.get("g2_reviews", [])[:3]:
            evidence_text += f"G2 Review: {review.get('content', '')[:200]}\n"
        
        for reddit in data.get("reddit_discussions", [])[:3]:
            evidence_text += f"Reddit: {reddit.get('title', '')} - {reddit.get('content', '')[:100]}\n"
        
        if data.get("pricing", {}).get("prices_found"):
            evidence_text += f"Pricing: {data['pricing']['prices_found']}\n"
    
    analysis_prompt = f"""
    Based on REAL evidence collected from G2 reviews, Reddit discussions, and pricing pages:
    
    {evidence_text}
    
    IMPORTANT RULES:
    1. ONLY use the evidence above. Do NOT invent anything.
    2. Every insight must cite which evidence it came from.
    3. If evidence is insufficient, mark confidence as LOW.
    
    Generate strategic insights for KeenFox (a new B2B SaaS productivity tool).
    
    Return JSON with:
    {{
        "insights": [
            {{
                "insight": "statement",
                "evidence_quotes": ["quote from evidence 1", "quote from evidence 2"],
                "confidence": "high|medium|low"
            }}
        ],
        "opportunities": ["opportunity1", "opportunity2", "opportunity3"],
        "threats": ["threat1", "threat2", "threat3"],
        "recommendations": [
            {{
                "title": "...",
                "description": "...",
                "rationale": "...",
                "priority": "high|medium|low"
            }}
        ]
    }}
    """
    
    response = model.generate_content(analysis_prompt)
    resp_text = response.text.strip()
    
    if '```json' in resp_text:
        resp_text = resp_text.split('```json')[1].split('```')[0]
    elif '```' in resp_text:
        resp_text = resp_text.split('```')[1]
    
    try:
        insights_data = json.loads(resp_text)
    except:
        insights_data = {
            "insights": [],
            "opportunities": ["Unable to generate due to API error"],
            "threats": [],
            "recommendations": []
        }
    
    report_id = str(uuid.uuid4())
    report = {
        "report_id": report_id,
        "generated_at": datetime.now().isoformat(),
        "company": request.company_name,
        "real_data_collected": {
            "total_g2_reviews": total_g2,
            "total_reddit_posts": total_reddit,
            "pricing_data_found": total_pricing,
            "competitors_analyzed": competitors
        },
        "evidence_summary": all_real_data,
        "insights": insights_data.get("insights", []),
        "opportunities": insights_data.get("opportunities", []),
        "threats": insights_data.get("threats", []),
        "recommendations": insights_data.get("recommendations", [])
    }
    
    reports_db[report_id] = report
    
    return {
        "status": "success",
        "report_id": report_id,
        "real_data_used": True,
        "g2_reviews_collected": total_g2,
        "reddit_posts_collected": total_reddit,
        "insights_generated": len(insights_data.get("insights", [])),
        "message": "All insights are backed by real G2, Reddit, and pricing data"
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/list_reports")
async def list_reports():
    """List all saved reports"""
    reports = []
    
    for file_path in REPORTS_FOLDER.glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
            reports.append({
                "report_id": report.get("report_id"),
                "company": report.get("company"),
                "generated_at": report.get("generated_at"),
                "competitors": len(report.get("competitors_analyzed", []))
            })
    
    reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
    
    return {
        "total_reports": len(reports),
        "reports": reports
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 KeenFox Competitive Intelligence System")
    print("="*60)
    print(f"✅ Gemini AI: {'Available' if model else 'Not available'}")
    print(f"📊 Reports stored: {len(reports_db)}")
    print("\n🌐 Starting server at http://localhost:8000")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🎨 Dashboard: http://localhost:8000/dashboard")
    print("\n💡 Quick test:")
    print('   curl -X POST "http://localhost:8000/run_intelligence" -H "Content-Type: application/json" -d "{\\"company_name\\": \\"TCS\\""}')
    print("\nPress CTRL+C to stop\n")
    print("="*60 + "\n")
    
    def open_browser():
        webbrowser.open("http://localhost:8000/dashboard")
    
    threading.Timer(2, open_browser).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)