# 🚀 AI-Powered Competitive Intelligence & Campaign Feedback System

## 🔍 Overview

This project is a **data-driven AI system** that continuously gathers competitor signals and transforms them into **actionable go-to-market (GTM) strategy recommendations**.

Unlike basic LLM tools, this system:

* Uses **real-world data (Reddit, G2, pricing pages)**
* Extracts **structured intelligence (features, sentiment, pricing)**
* Applies **AI reasoning to generate strategic insights**

---

## 🎯 Problem Solved

Manual competitor tracking is slow and reactive.
This system automates:

* Competitor monitoring
* Market signal analysis
* Campaign strategy improvement

👉 Result: **Faster, data-driven decision making**

---

## 🧠 Key Capabilities

### 📊 Competitive Intelligence Engine

* Discovers 5–7 competitors dynamically
* Extracts:

  * Feature launches
  * Customer sentiment (Reddit + G2)
  * Pricing insights
  * Strengths, weaknesses, opportunities, threats
* Identifies **market gaps and positioning opportunities**

---

### 📢 Campaign Feedback Loop

* Generates **messaging improvements** (with sample copy)
* Recommends **channel strategy**
* Produces **3–5 GTM strategic actions with rationale**

---

### 🔁 Bonus Features

* “What changed” diff analysis between runs
* Natural language Q&A over intelligence reports
* Interactive dashboard UI

---

## ⚙️ System Architecture

**3-Layer Architecture:**

1. **Presentation Layer**

   * Dashboard (HTML/CSS/JS)
   * Swagger UI
   * API clients

2. **Application Layer**

   * FastAPI backend
   * Intelligence Engine:

     * Competitor discovery
     * SWOT analysis
     * Campaign recommendation

3. **Data + AI Layer**

   * Reddit API (120+ posts)
   * G2 reviews
   * Pricing pages
   * Gemini 2.5 Flash (reasoning engine)

---

## 🔄 Data Flow

1. Collect competitor data (Reddit, G2, web)
2. Clean & filter noisy signals
3. Extract features & sentiment
4. Pass structured data to LLM
5. Generate:

   * Insights
   * SWOT
   * Strategy recommendations
6. Store report + enable diff analysis

---

## 🧠 AI Strategy (Important)

The system is designed to **reason, not just summarize**:

* Uses role-based prompts (“You are a product strategist”)
* Performs **comparative analysis across competitors**
* Generates **actionable recommendations**, not descriptions

👉 This ensures output is **decision-ready**, not generic text

---

## 📊 Sample Output (Real Insight)

```json
{
  "competitor": "Notion",
  "insight": "Users love flexibility but complain about complexity",
  "gap_detected": "Steep learning curve for new users",
  "recommendation": {
    "messaging": "Position KeenFox as simpler and faster alternative",
    "channel": "Target Reddit and startup communities",
    "gtm_strategy": [
      "Highlight ease-of-use in campaigns",
      "Target users switching from Notion",
      "Promote onboarding simplicity"
    ]
  }
}
```

---

## ⚙️ Tech Stack

* **FastAPI** → backend API
* **Gemini 2.5 Flash** → AI reasoning
* **Reddit API + BeautifulSoup** → data ingestion
* **HTML/CSS/JS** → dashboard UI

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
python main.py
```

Open:

* Dashboard → http://localhost:8000/dashboard
* API Docs → http://localhost:8000/docs

---

## 📡 API Endpoints

* POST `/discover_competitors`
* POST `/run_intelligence`
* GET `/get_report`
* POST `/ask_question`
* GET `/what_changed`
* GET `/dashboard`

---

## ⚡ Performance

* Competitor Discovery: 2–3 seconds
* Full Intelligence Report: 15–20 seconds
* Q&A Response: 2–3 seconds

---

## ⚠️ Limitations

* Limited real-time data scraping
* API rate limits (fallback logic used)
* In-memory storage (not persistent)

---

## 🚀 Future Improvements

* Vector database for semantic search
* Real-time streaming pipelines
* Scalable storage (PostgreSQL)
* Advanced dashboard analytics

---

## 👤 Author

Harini Dharanikota

## 📅 Date

April 2026
