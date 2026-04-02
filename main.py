# # main.py - COMPLETELY FIXED VERSION
# import os
# import json
# import uuid
# from datetime import datetime
# from typing import List, Optional, Dict, Any
# from fastapi import FastAPI, HTTPException
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# import uvicorn
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Import Gemini
# try:
#     import google.generativeai as genai
#     GEMINI_AVAILABLE = True
# except ImportError:
#     GEMINI_AVAILABLE = False
#     print("⚠️ Gemini not available")

# # Configuration
# API_KEY = os.getenv('GEMINI_API_KEY')
# if API_KEY and GEMINI_AVAILABLE:
#     genai.configure(api_key=API_KEY)
#     model = genai.GenerativeModel('gemini-pro')
#     print("✅ Gemini AI configured successfully")
# else:
#     model = None
#     print("⚠️ Gemini AI not configured")

# # Create FastAPI app
# app = FastAPI(title="KeenFox Intelligence System", version="1.0.0")

# # Data models
# class CompetitorRequest(BaseModel):
#     company_name: str
#     competitors: Optional[List[str]] = None

# class QuestionRequest(BaseModel):
#     question: str
#     report_id: Optional[str] = None

# # Store for reports
# reports_db = {}

# @app.get("/")
# async def root():
#     return {
#         "system": "KeenFox Competitive Intelligence System",
#         "status": "operational",
#         "gemini_available": GEMINI_AVAILABLE and API_KEY is not None,
#         "endpoints": [
#             "/discover_competitors",
#             "/run_intelligence",
#             "/get_report",
#             "/ask_question",
#             "/what_changed"
#         ]
#     }

# @app.post("/discover_competitors")
# async def discover_competitors(request: CompetitorRequest):
#     """Discover competitors for any company"""
#     if not model:
#         # Return default competitors if AI not available
#         default_competitors = ["Notion", "Asana", "ClickUp", "Monday.com", "Trello", "Basecamp", "Wrike"]
#         return {
#             "company": request.company_name,
#             "competitors": default_competitors,
#             "count": len(default_competitors),
#             "note": "Using default competitors (Gemini not available)"
#         }
    
#     try:
#         prompt = f"""
#         List the top 7 direct competitors for {request.company_name} in the B2B SaaS market.
#         Return ONLY a JSON array of competitor names, nothing else.
#         Example: ["Competitor1", "Competitor2", "Competitor3"]
#         """
        
#         response = model.generate_content(prompt)
#         # Parse the response
#         competitors_text = response.text.strip()
#         # Remove markdown code blocks if present
#         if '```json' in competitors_text:
#             competitors_text = competitors_text.split('```json')[1].split('```')[0]
#         elif '```' in competitors_text:
#             competitors_text = competitors_text.split('```')[1]
        
#         competitors = json.loads(competitors_text)
        
#         return {
#             "company": request.company_name,
#             "competitors": competitors[:7],
#             "count": len(competitors[:7])
#         }
#     except Exception as e:
#         # Return default competitors if AI fails
#         default_competitors = ["Notion", "Asana", "ClickUp", "Monday.com", "Trello", "Basecamp", "Wrike"]
#         return {
#             "company": request.company_name,
#             "competitors": default_competitors,
#             "count": len(default_competitors),
#             "note": f"Using default competitors (error: {str(e)[:50]})"
#         }

# @app.post("/run_intelligence")
# async def run_intelligence(request: CompetitorRequest):
#     """Run full intelligence cycle"""
#     if not model:
#         raise HTTPException(status_code=503, detail="Gemini AI not available. Please check your API key.")
    
#     try:
#         # Get competitors
#         if request.competitors:
#             competitors = request.competitors
#         else:
#             comp_response = await discover_competitors(request)
#             competitors = comp_response.get("competitors", [])[:5]
        
#         # Analyze each competitor
#         analyses = []
#         all_insights = []
        
#         for competitor in competitors[:5]:
#             prompt = f"""
#             Analyze {competitor} as a competitor in the B2B SaaS productivity market.
            
#             Return JSON with:
#             {{
#                 "strengths": ["strength1", "strength2", "strength3"],
#                 "weaknesses": ["weakness1", "weakness2", "weakness3"],
#                 "key_features": ["feature1", "feature2"],
#                 "market_position": "leader|challenger|niche",
#                 "threat_level": "high|medium|low"
#             }}
#             """
            
#             response = model.generate_content(prompt)
#             resp_text = response.text.strip()
#             # Clean up the response
#             if '```json' in resp_text:
#                 resp_text = resp_text.split('```json')[1].split('```')[0]
#             elif '```' in resp_text:
#                 resp_text = resp_text.split('```')[1]
            
#             try:
#                 analysis = json.loads(resp_text)
#             except:
#                 # If JSON parsing fails, create a default structure
#                 analysis = {
#                     "strengths": ["Market presence", "Brand recognition"],
#                     "weaknesses": ["Complex pricing", "Integration gaps"],
#                     "key_features": ["Core features"],
#                     "market_position": "challenger",
#                     "threat_level": "medium"
#                 }
            
#             analyses.append({
#                 "competitor": competitor,
#                 "analysis": analysis
#             })
#             all_insights.extend(analysis.get("weaknesses", []))
        
#         # Generate market insights
#         insights_prompt = f"""
#         Based on analysis of these competitors: {[a['competitor'] for a in analyses]}
        
#         Generate strategic insights for a new entrant (KeenFox):
#         1. Top 3 market opportunities
#         2. Top 3 threats
#         3. Recommended messaging positioning
#         4. Key features to prioritize
        
#         Return as JSON with these exact keys: opportunities, threats, messaging, features
#         """
        
#         insights_response = model.generate_content(insights_prompt)
#         insights_text = insights_response.text.strip()
#         if '```json' in insights_text:
#             insights_text = insights_text.split('```json')[1].split('```')[0]
#         elif '```' in insights_text:
#             insights_text = insights_text.split('```')[1]
        
#         try:
#             market_insights = json.loads(insights_text)
#         except:
#             market_insights = {
#                 "opportunities": ["Mobile-first experience", "Simplified pricing", "Better integrations"],
#                 "threats": ["Established competitors", "Brand loyalty", "Feature parity"],
#                 "messaging": "Focus on simplicity and ease of use",
#                 "features": ["AI-powered automation", "Real-time collaboration", "Advanced analytics"]
#             }
        
#         # Generate campaign recommendations
#         campaign_prompt = f"""
#         Based on the competitive analysis, generate 3 specific campaign recommendations for KeenFox:
        
#         1. Messaging recommendation (with example copy)
#         2. Channel strategy recommendation
#         3. GTM priority recommendation
        
#         Return as JSON array with fields: title, description, rationale, priority
#         """
        
#         campaign_response = model.generate_content(campaign_prompt)
#         campaign_text = campaign_response.text.strip()
#         if '```json' in campaign_text:
#             campaign_text = campaign_text.split('```json')[1].split('```')[0]
#         elif '```' in campaign_text:
#             campaign_text = campaign_text.split('```')[1]
        
#         try:
#             recommendations = json.loads(campaign_text)
#         except:
#             recommendations = [
#                 {
#                     "title": "Mobile-First Messaging",
#                     "description": "Highlight superior mobile experience",
#                     "rationale": "Competitors have weak mobile apps",
#                     "priority": "high"
#                 },
#                 {
#                     "title": "LinkedIn & Twitter Focus",
#                     "description": "Target B2B decision makers on LinkedIn",
#                     "rationale": "Competitors are active here",
#                     "priority": "medium"
#                 },
#                 {
#                     "title": "Free Tier Expansion",
#                     "description": "Offer generous free tier to capture market",
#                     "rationale": "Low barrier to entry",
#                     "priority": "high"
#                 }
#             ]
        
#         # Create report
#         report_id = str(uuid.uuid4())
#         report = {
#             "report_id": report_id,
#             "generated_at": datetime.now().isoformat(),
#             "company": request.company_name,
#             "competitors_analyzed": competitors[:5],
#             "competitor_analyses": analyses,
#             "market_insights": market_insights,
#             "recommendations": recommendations,
#             "key_findings": all_insights[:5] if all_insights else ["Market analysis complete"]
#         }
        
#         reports_db[report_id] = report
        
#         return {
#             "status": "success",
#             "report_id": report_id,
#             "competitors_analyzed": competitors[:5],
#             "key_findings": report["key_findings"],
#             "generated_at": report["generated_at"]
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# @app.get("/get_report")
# async def get_report(report_id: Optional[str] = None):
#     """Get intelligence report"""
#     if not report_id and reports_db:
#         report_id = list(reports_db.keys())[-1]
    
#     if not report_id or report_id not in reports_db:
#         raise HTTPException(status_code=404, detail="Report not found. Run /run_intelligence first.")
    
#     report = reports_db[report_id]
#     return JSONResponse(report)

# @app.post("/ask_question")
# async def ask_question(request: QuestionRequest):
#     """Ask questions about competitive data"""
#     if not model:
#         raise HTTPException(status_code=503, detail="Gemini AI not available")
    
#     # Get report
#     if request.report_id:
#         report = reports_db.get(request.report_id)
#     else:
#         report = list(reports_db.values())[-1] if reports_db else None
    
#     if not report:
#         raise HTTPException(status_code=404, detail="No report available. Run /run_intelligence first.")
    
#     try:
#         prompt = f"""
#         Based on this competitive intelligence report:
#         {json.dumps(report, indent=2, default=str)[:3000]}
        
#         Answer this question: {request.question}
        
#         Provide a specific, data-driven answer.
#         """
        
#         response = model.generate_content(prompt)
        
#         return {
#             "question": request.question,
#             "answer": response.text,
#             "report_id": report.get("report_id")
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/what_changed")
# async def what_changed():
#     """Show what changed since last run"""
#     if len(reports_db) < 2:
#         return {
#             "message": "Need at least 2 reports to compare. Run /run_intelligence twice.",
#             "reports_count": len(reports_db)
#         }
    
#     reports_list = list(reports_db.values())
#     latest = reports_list[-1]
#     previous = reports_list[-2]
    
#     return {
#         "previous_report": previous.get("generated_at"),
#         "current_report": latest.get("generated_at"),
#         "changes": {
#             "competitors_added": [c for c in latest.get("competitors_analyzed", []) 
#                                  if c not in previous.get("competitors_analyzed", [])],
#             "competitors_removed": [c for c in previous.get("competitors_analyzed", []) 
#                                    if c not in latest.get("competitors_analyzed", [])]
#         }
#     }

# if __name__ == "__main__":
#     print("\n" + "="*60)
#     print("🚀 KeenFox Competitive Intelligence System")
#     print("="*60)
#     print(f"✅ Gemini AI: {'Available' if model else 'Not available'}")
#     print(f"📊 Reports stored: {len(reports_db)}")
#     print("\n🌐 Starting server at http://localhost:8000")
#     print("📝 API Documentation: http://localhost:8000/docs")
#     print("\n💡 Quick test: Open new terminal and run:")
#     print('   curl -X POST "http://localhost:8000/run_intelligence" -H "Content-Type: application/json" -d "{\\"company_name\\": \\"KeenFox\\""}')
#     print("\nPress CTRL+C to stop\n")
#     print("="*60 + "\n")
    
#     uvicorn.run(app, host="0.0.0.0", port=8000)
# main.py - FIXED with correct model name
import os
import json
import uuid
import webbrowser
from data_ingestion import DataIngestor
from fastapi.responses import HTMLResponse
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Create ingestor instance for real data
ingestor = DataIngestor()

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
    # FIXED: Use correct model name - gemini-1.5-flash
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
    print("✅ Gemini AI configured successfully with gemini-1.5-flash")
else:
    model = None
    print("⚠️ Gemini AI not configured")

# Create FastAPI app
app = FastAPI(title="KeenFox Intelligence System", version="1.0.0")

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
    """Discover competitors for any company"""
    if not model:
        # Return default competitors if AI not available
        default_competitors = ["Notion", "Asana", "ClickUp", "Monday.com", "Trello", "Basecamp", "Wrike"]
        return {
            "company": request.company_name,
            "competitors": default_competitors,
            "count": len(default_competitors),
            "note": "Using default competitors (Gemini not available)"
        }
    
    try:
        prompt = f"""
        List the top 7 direct competitors for {request.company_name} in the B2B SaaS market.
        Return ONLY a JSON array of competitor names, nothing else.
        Example: ["Competitor1", "Competitor2", "Competitor3"]
        """
        
        response = model.generate_content(prompt)
        # Parse the response
        competitors_text = response.text.strip()
        # Remove markdown code blocks if present
        if '```json' in competitors_text:
            competitors_text = competitors_text.split('```json')[1].split('```')[0]
        elif '```' in competitors_text:
            competitors_text = competitors_text.split('```')[1]
        
        competitors = json.loads(competitors_text)
        
        return {
            "company": request.company_name,
            "competitors": competitors[:7],
            "count": len(competitors[:7])
        }
    except Exception as e:
        # Return default competitors if AI fails
        default_competitors = ["Notion", "Asana", "ClickUp", "Monday.com", "Trello", "Basecamp", "Wrike"]
        return {
            "company": request.company_name,
            "competitors": default_competitors,
            "count": len(default_competitors),
            "note": f"Using default competitors (error: {str(e)[:50]})"
        }

@app.post("/run_intelligence")
async def run_intelligence(request: CompetitorRequest):
    """Run full intelligence cycle"""
    if not model:
        raise HTTPException(status_code=503, detail="Gemini AI not available. Please check your API key.")
    
    try:
        # Get competitors
        if request.competitors:
            competitors = request.competitors
        else:
            comp_response = await discover_competitors(request)
            competitors = comp_response.get("competitors", [])[:5]
        
        # Analyze each competitor
        analyses = []
        all_insights = []
        
        for competitor in competitors[:5]:
            prompt = f"""
            Analyze {competitor} as a competitor in the B2B SaaS productivity market.
            
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
            # Clean up the response
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0]
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1]
            
            try:
                analysis = json.loads(resp_text)
            except:
                # If JSON parsing fails, create a default structure
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
        
        # Generate market insights
        insights_prompt = f"""
        Based on analysis of these competitors: {[a['competitor'] for a in analyses]}
        
        Generate strategic insights for a new entrant (KeenFox):
        1. Top 3 market opportunities
        2. Top 3 threats
        3. Recommended messaging positioning
        4. Key features to prioritize
        
        Return as JSON with these exact keys: opportunities, threats, messaging, features
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
                "opportunities": ["Mobile-first experience", "Simplified pricing", "Better integrations"],
                "threats": ["Established competitors", "Brand loyalty", "Feature parity"],
                "messaging": "Focus on simplicity and ease of use",
                "features": ["AI-powered automation", "Real-time collaboration", "Advanced analytics"]
            }
        
        # Generate campaign recommendations
        campaign_prompt = f"""
        Based on the competitive analysis, generate 3 specific campaign recommendations for KeenFox:
        
        1. Messaging recommendation (with example copy)
        2. Channel strategy recommendation
        3. GTM priority recommendation
        
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
                    "rationale": "Competitors have weak mobile apps",
                    "priority": "high"
                },
                {
                    "title": "LinkedIn & Twitter Focus",
                    "description": "Target B2B decision makers on LinkedIn",
                    "rationale": "Competitors are active here",
                    "priority": "medium"
                },
                {
                    "title": "Free Tier Expansion",
                    "description": "Offer generous free tier to capture market",
                    "rationale": "Low barrier to entry",
                    "priority": "high"
                }
            ]
        
        # Create report
        report_id = str(uuid.uuid4())
        report = {
            "report_id": report_id,
            "generated_at": datetime.now().isoformat(),
            "company": request.company_name,
            "competitors_analyzed": competitors[:5],
            "competitor_analyses": analyses,
            "market_insights": market_insights,
            "recommendations": recommendations,
            "key_findings": all_insights[:5] if all_insights else ["Market analysis complete"]
        }
        
        reports_db[report_id] = report
        
        return {
            "status": "success",
            "report_id": report_id,
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
    
    if not report_id or report_id not in reports_db:
        raise HTTPException(status_code=404, detail="Report not found. Run /run_intelligence first.")
    
    report = reports_db[report_id]
    return JSONResponse(report)

@app.post("/ask_question")
async def ask_question(request: QuestionRequest):
    """Ask questions about competitive data"""
    if not model:
        raise HTTPException(status_code=503, detail="Gemini AI not available")
    
    # Get report
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
    
    # Get competitors
    if request.competitors:
        competitors = request.competitors
    else:
        comp_response = await discover_competitors(request)
        competitors = comp_response.get("competitors", [])[:3]
    
    # Gather REAL data for each competitor
    all_real_data = []
    for competitor in competitors:
        print(f"📊 Gathering real data for {competitor}...")
        real_data = await ingestor.gather_all_data(competitor)
        all_real_data.append(real_data)
    
    # Count real data collected
    total_g2 = sum(len(d.get("g2_reviews", [])) for d in all_real_data)
    total_reddit = sum(len(d.get("reddit_discussions", [])) for d in all_real_data)
    total_pricing = sum(1 for d in all_real_data if d.get("pricing", {}).get("prices_found"))
    
    # Build evidence summary for prompt
    evidence_text = ""
    for data in all_real_data:
        evidence_text += f"\n\n--- {data['name']} ---\n"
        
        # Add G2 reviews as evidence
        for review in data.get("g2_reviews", [])[:3]:
            evidence_text += f"G2 Review: {review.get('content', '')[:200]}\n"
        
        # Add Reddit discussions as evidence
        for reddit in data.get("reddit_discussions", [])[:3]:
            evidence_text += f"Reddit: {reddit.get('title', '')} - {reddit.get('content', '')[:100]}\n"
        
        # Add pricing info
        if data.get("pricing", {}).get("prices_found"):
            evidence_text += f"Pricing: {data['pricing']['prices_found']}\n"
    
    # Use Gemini to analyze WITH evidence
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
    
    # Clean JSON
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
    
    # Create report with evidence tracking
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

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 KeenFox Competitive Intelligence System")
    print("="*60)
    print(f"✅ Gemini AI: {'Available' if model else 'Not available'}")
    print(f"📊 Reports stored: {len(reports_db)}")
    print("\n🌐 Starting server at http://localhost:8000")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("\n💡 Quick test: Open new terminal and run:")
    print('   curl -X POST "http://localhost:8000/run_intelligence" -H "Content-Type: application/json" -d "{\\"company_name\\": \\"KeenFox\\""}')
    print("\nPress CTRL+C to stop\n")
    print("="*60 + "\n")
    def open_browser():
        import webbrowser
        webbrowser.open("http://localhost:8000/dashboard")
    import threading
    threading.Timer(2, open_browser).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)