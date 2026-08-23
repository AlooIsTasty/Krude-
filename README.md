# Krude: Sovereign Energy Supply Chain & Maritime Geopolitical Risk Digital Twin

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.0+-FFF000.svg?style=flat&logo=duckdb)](https://duckdb.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.0+-blue.svg?style=flat)](https://networkx.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Empirical decision-support platform and geospatial digital twin that continuously monitors global maritime chokepoints, models kinetic supply disruption shocks, quantifies macroeconomic transmission into India's fiscal balance, and autonomously orchestrates optimal crude procurement rerouting and Strategic Petroleum Reserve (ISPRL) drawdowns.**

---

##  1. Executive Summary & The Problem Solved

India is the world's 3rd largest consumer of crude oil, consuming approximately **5.4 Million Barrels per Day (MBPD)** with a staggering **88% net import dependency**. 

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INDIA'S ENERGY SECURITY VULNERABILITY                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  • 88% Net Crude Import Dependency (~4.75 MBPD Imported)                    │
│  • 40–45% of total crude imports transit the narrow Strait of Hormuz        │
│  • Secondary maritime choke exposure at Bab-el-Mandeb & Malacca             │
│  • Total Strategic Petroleum Reserve (ISPRL) cover is ~9.5 days (~39 MMBBL) │
│  • Every +$10/bbl crude spike adds ~$14.2B to annual import bill & +54 bps  │
│    Current Account Deficit (CAD) widening                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Problem
Traditional energy security risk monitoring operates in fragmented silos:
1. **Geopolitical risk tracking** relies on delayed news summaries without quantitative impact models.
2. **Maritime logistics** lack dynamic landed-cost optimization that factors in war-risk insurance, freight surcharges, and searoute transit delays (e.g. +14 to +17 days via the Cape of Good Hope).
3. **Refinery compatibility constraints** (API gravity, sulfur limits, Nelson complexity) are rarely paired with real-time supplier availability.
4. **Strategic Petroleum Reserve (SPR) cavern releases** lack risk-calibrated optimization models to prevent premature exhaustion during prolonged maritime interdictions.

### The Solution: Krude Digital Twin
**Krude** unifies real-time intelligence ingestion, fine-tuned neural reasoning, linear programming (LP) optimization, macroeconomic waterfall simulation, and multi-cavern SPR management into a single, high-performance digital twin.

---

##  2. High-Level System Architecture

```
                                  LIVE GLOBAL DATA FEEDS
                    ┌─────────────────────────────────────────────────┐
                    │ GDELT 2.0 • NewsAPI • Vortexa AIS • PPAC India  │
                    └───────────────────────┬─────────────────────────┘
                                            │
                                            ▼
                    ┌─────────────────────────────────────────────────┐
                    │   LIVE INTELLIGENCE & SENTIMENT INGESTION       │
                    │   • Parallel corridor multi-threading (NewsAPI) │
                    │   • Background Stale-While-Revalidate caching   │
                    │   • Multi-lingual maritime keyword extraction   │
                    └───────────────────────┬─────────────────────────┘
                                            │
                                            ▼
                    ┌─────────────────────────────────────────────────┐
                    │         KRUDEAI NEURAL REASONING ENGINE         │
                    │   • Fine-Tuned Llama-3 / Mistral (Local Ollama) │
                    │   • 5-Stage Risk Pipeline: Dedupe → Time Decay  │
                    │     → Noisy-OR Aggregation → Momentum → Alerts  │
                    │   • Ultra-fast heuristic fallback (<25ms)       │
                    └───────────────────────┬─────────────────────────┘
                                            │
                                            ▼
                    ┌─────────────────────────────────────────────────┐
                    │    MACROECONOMIC DISRUPTION TRANSMISSION        │
                    │   • Physical Barrel Deficit Calculator          │
                    │   • Freight & War-Risk Surcharge Models         │
                    │   • GDP Headwinds & CAD Multipliers (DuckDB)    │
                    └───────┬─────────────────────────────────┬───────┘
                            │                                 │
            ┌───────────────┴──────────────┐   ┌──────────────┴──────────────┐
            ▼                              ▼   ▼                             ▼
┌───────────────────────────────┐   ┌────────────────────────────────────────┐
│ ADAPTIVE PROCUREMENT ENGINE   │   │  STRATEGIC PETROLEUM RESERVE (ISPRL)   │
│ • Landed Cost Optimizer (PuLP)│   │  • Multi-Cavern Allocation (Visakh,    │
│ • API & Sulfur Blending       │   │    Mangalore, Padur)                   │
│ • 8 Strategic Bypass Routes   │   │  • Dynamic Risk-Synced Drawdown        │
└───────────────┬───────────────┘   └─────────────────┬──────────────────────┘
                │                                     │
                └──────────────────┬──────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────────────────┐
                    │  MARITIME SUPPLY CHAIN DIGITAL TWIN DASHBOARD   │
                    │  • Interactive NetworkX Curved Oceanic Routes   │
                    │  • Isolated Chokepoint Interdiction Waves       │
                    │  • Ultra-Responsive Glassmorphic UI (Vanilla JS)│
                    └─────────────────────────────────────────────────┘
```

---

##  3. Key Modules & Features

### 1.  Live Geopolitical Risk Board & Intelligence Feed
* **Live Corridors Monitored**: Strait of Hormuz, Bab-el-Mandeb, Suez Canal, Malacca Strait, Cape of Good Hope.
* **Non-Blocking Background Caching**: Response times optimized down to **`<25 ms`** using background pre-fetching and thread pooling.
* **Corridor-Specific Threat Score ($0 - 10$)**: Normalized risk scores calculated using Noisy-OR aggregation and exponential time decay ($\lambda = 0.05/\text{day}$).

### 2.  KrudeAi Neural Inference Sandbox (`/api/model/analyze`)
* Evaluates arbitrary maritime news headlines and returns quantitative threat scores ($0 - 10$), corridor-specific geopolitical reasoning, and token latency.
* Dual-mode architecture: Runs against fine-tuned local weights via Ollama or executes instantly via high-speed semantic fallback ($<25\text{ms}$).

### 3.  Disruption Scenario Simulator & Macro Transmission Waterfall
* Simulates custom interdiction scenarios across any corridor (e.g. 80% Hormuz closure for 45 days).
* **Quantified Outputs**:
  - Physical supply deficit ($\text{MBPD}$).
  - Cape of Good Hope rerouting delay ($+14\text{ to }+17\text{ days}$).
  - Landed crude cost surge ($\Delta \$/\text{bbl}$).
  - India import bill addition ($\$ \text{Billion}$).
  - Macroeconomic impact: Real GDP growth headwind ($\Delta \text{pp}$) and CAD widening ($\text{bps}$).

### 4.  Adaptive Procurement Orchestrator
* Evaluates and dynamically ranks alternative supply corridors to replace interdicted Persian Gulf crude:
  1. **Brazil (Santos Basin / Tupi FPSO)** — Cape of Good Hope ($71.15/\text{bbl}$, 28d transit, $+340\text{ kbd}$)
  2. **UAE (Fujairah Deepwater Hub)** — ADCOP Pipeline Hormuz Bypass ($74.20/\text{bbl}$, 4d transit, $+500\text{ kbd}$)
  3. **Oman (Duqm / Mina Al Fahal)** — Direct Arabian Sea Bypass ($73.10/\text{bbl}$, 7d transit, $+260\text{ kbd}$)
  4. **Saudi Arabia (Yanbu Red Sea Terminal)** — Petroline Pipeline Bypass ($72.80/\text{bbl}$, 12d transit, $+450\text{ kbd}$)
  5. **Nigeria (Bonny Offshore Terminal)** — Atlantic Sweet ($73.80/\text{bbl}$, 25d transit, $+280\text{ kbd}$)
  6. **USA (Corpus Christi / LOOP)** — WTI Midland via Cape ($74.51/\text{bbl}$, 38d transit, $+300\text{ kbd}$)
  7. **Russia (Kozmino Pacific Port)** — ESPO Blend via Malacca ($76.40/\text{bbl}$, 18d transit, $+350\text{ kbd}$)
  8. **Iraq (Ceyhan Mediterranean Hub)** — Kirkuk-Ceyhan Pipeline Bypass ($75.90/\text{bbl}$, 24d transit, $+220\text{ kbd}$)

### 5.  Strategic Petroleum Reserve (ISPRL) Drawdown Optimizer
* Manages India's **39.28 MMBBL (5.33 MMT)** underground rock caverns across 3 strategic locations:
  - **Visakhapatnam (Andhra Pradesh)**: $1.33\text{ MMT}$ ($9.77\text{ MMBBL}$)
  - **Mangalore (Karnataka)**: $1.50\text{ MMT}$ ($11.00\text{ MMBBL}$)
  - **Padur (Karnataka)**: $2.50\text{ MMT}$ ($18.51\text{ MMBBL}$)
* **Interactive Drawdown Policies**:
  - **Steady Linear Release** ($180\text{ kbd}$ · 52-day coverage).
  - **Aggressive Price Arrest** ($350\text{ kbd}$ · 28-day coverage).
  - **Hold & Conserve** ($65\text{ kbd}$ · 140+ day coverage).
  - **Sync Live Risk**: Dynamically calculates optimal drawdown rate based on active real-time corridor threat scores.

### 6.  Maritime Supply Chain Digital Twin
* World-scale NetworkX maritime route graph rendered with smooth quadratic bezier curved paths across ocean basins.
* **Corridor-Isolated Interdiction**: Triggering a cascade on a chokepoint specifically highlights only the affected maritime lanes and discharge ports in pulsing alert red, leaving unaffected lanes calm.

---

##  4. Mathematical Formulations & Optimization Models

### A. Multi-Criteria Supplier Optimization Score
$$S_i = 0.4 \cdot \tilde{C}_i + 0.3 \cdot \left(\frac{R_c}{10}\right) + 0.2 \cdot \tilde{T}_i + 0.1 \cdot (1 - \tilde{K}_i)$$

Where:
* $\tilde{C}_i$: Min-max normalized landed cost ($\$/\text{bbl}$).
* $R_c$: Active threat score of the transit corridor ($0 - 10$).
* $\tilde{T}_i$: Min-max normalized searoute transit duration (days).
* $\tilde{K}_i$: Min-max normalized spare production capacity ($\text{MBPD}$).
* *Optimization Objective*: $\min S_i$ (Lower composite score = higher procurement priority).

### B. Total Landed Crude Cost Model
$$C_{\text{landed}} = C_{\text{FOB}} + F_{\text{base}} \cdot \left(1 + \frac{D_{\text{transit}}}{25}\right) + \text{Ins}_{\text{war}}(R_c) + \text{Demurrage}_{\text{choke}}$$

### C. Noisy-OR Threat Aggregation with Exponential Decay
$$P(\text{Disruption} \mid \text{Corridor } c) = 1 - \prod_{j=1}^{N} \left(1 - P(E_j) \cdot e^{-\lambda(t - t_j)}\right)$$

Where $\lambda = 0.05/\text{day}$, giving older events a natural half-life decay of $\approx 13.8\text{ days}$.

---

##  5. Technology Stack

### Backend
* **Language**: Python 3.10+
* **Framework**: FastAPI (Asynchronous ASGI REST API)
* **Server**: Uvicorn
* **Database & Analytics**: DuckDB (Embedded OLAP engine), SQLite
* **Graph Algorithms**: NetworkX
* **Mathematical Optimization**: PuLP (Linear Programming CBC solver)
* **Machine Learning / LLM**: Fine-tuned Llama-3/Mistral instruction adapter via Ollama / HuggingFace Transformers

### Frontend
* **Core**: HTML5, Vanilla JavaScript (ES6+), Vanilla CSS (Custom Nixtio Dark Design System)
* **Visualizations**: Chart.js 4.4, Dynamic Scalable SVG vector canvases
* **Styling**: Glassmorphism, CSS Custom Properties, Responsive CSS Grid, Smooth Staggered Scroll Transitions (IntersectionObserver)
* **Icons & Fonts**: FontAwesome 6, Google Fonts (Syne, Plus Jakarta Sans, JetBrains Mono)

---

##  6. Step-by-Step Installation & Local Setup

### Prerequisites
* **Python 3.10, 3.11, or 3.12** installed on your system.
* **Git** installed.
* *(Optional)* **Ollama** installed if running local neural LLM weights.

### 1. Clone the Repository
```bash
git clone https://github.com/AlooIsTasty/Krude-.git
cd Krude-
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (or edit the existing one):
```env
NEWS_API_KEY="your_news_api_key_here"
AI_API_KEY="your_ai_api_key_here"
PORT=8000
HOST="127.0.0.1"
```

### 5. Launch the Server & Dashboard
```bash
# Direct launcher
python run.py

# Or via FastAPI backend directly
python backend/main.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`**

Interactive OpenAPI / Swagger documentation:
👉 **`http://127.0.0.1:8000/docs`**

---

## 🔌 7. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/risk/scores` | Returns composite risk scores ($0 - 10$), threat levels, and active news signals across all corridors. |
| `GET` | `/api/risk/feed` | Returns deduplicated, sentiment-scored live maritime intelligence headlines with GDELT/NewsAPI provenance. |
| `POST` | `/api/risk/refresh` | Triggers background pre-caching and news re-aggregation. |
| `POST` | `/api/procurement/rank` | Executes multi-criteria ranking on global alternative crude suppliers for given corridor risk inputs. |
| `POST` | `/api/scenario/simulate` | Simulates physical barrel deficit, landed cost spike, macro GDP loss, and CAD widening for custom disruptions. |
| `POST` | `/api/model/analyze` | Evaluates arbitrary headlines using KrudeAi neural reasoning and outputs calibrated score + explanation. |
| `GET` | `/api/model/status` | Returns active model backend (Ollama / PyTorch / Fast Engine), device status, and metadata. |
| `GET` | `/api/data/macro-parameters` | Returns baseline Indian energy consumption, import dependency, and refinery capacities. |

---

##  8. Automated Test Suite

Run the full automated test suite (verifying risk calculation, scenario simulation, multi-criteria procurement ranking, and linear optimization):

```bash
python -m unittest backend/tests/test_engine.py
```

Output:
```
----------------------------------------------------------------------
Ran 13 tests in 4.141s

OK
[OK] Generated empirical validation plot -> backend/data/hormuz_18m_risk_plot.png
```

---

##  9. Authors & Team Credits

Built with by:
* **Pratik Phophaliya**
* **Lalmuankima Colney**
* **Mohak Chabbra**

---

##  10. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
