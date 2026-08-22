# Krude: India Energy Supply Chain & Geopolitical Risk Digital Twin

An AI-powered decision-support system and geospatial digital twin that continuously monitors geopolitical risk, models maritime disruption scenarios (e.g. Strait of Hormuz closure, Red Sea interdiction), quantifies macroeconomic impacts on India, and generates executable crude procurement rerouting and Strategic Petroleum Reserve (SPR) drawdown schedules.

---

## 🚀 Architecture & Live Model Deployment

```
                      INTERNET
                         │
                         ▼
                Antigravity website (Frontend Dashboard)
                         │
                         │ API requests (/api/risk/refresh, /api/model/analyze)
                         ▼
                  YOUR LAPTOP
                ┌──────────────────────────────────┐
                │ FastAPI Backend (Port 8000)      │
                │                                  │
                │ Llama 3.2 3B + LoRA (Krude-risk) │
                │ Source: C:\models\Krude          │
                │                                  │
                │ NVIDIA GeForce RTX 3050 GPU      │
                └──────────────────────────────────┘
```

1. **Fine-Tuned Llama 3.2 3B + LoRA Agent (REAL)**: Located in `C:\models\Krude`, registered in Ollama as `Krude-risk`. Evaluates live news headlines and outputs both numerical Risk Scores ($0 - 10$) and geopolitical reasoning.
2. **Disruption Scenario Modeller (SIMULATED)**: Simulates Hormuz and Red Sea shocks, calculating physical barrel deficits, Cape of Good Hope rerouting lag (+17 days), freight surges, and macroeconomic damage (India import bill delta, CPI inflation rise, GDP headwinds).
3. **Adaptive Procurement Orchestrator (REAL)**: Matches replacement global crude grades against Indian refinery Nelson complexity, API gravity, and sulfur limits with real Searoute marine distances.
4. **Strategic Reserve (SPR) Optimiser (SIMULATED)**: Solves multi-cavern inventory drawdown (Mangalore, Padur, Visakhapatnam, Chandikhol) to bridge supply gaps.
5. **Interactive 3D Earth Digital Twin**: Real-time dark-mode globe with live shipping corridors, chokepoints, and interactive Live AI Headline Inference Lab.

---

## 🛠️ How to Run This

### Step 1: Ensure Ollama is Running with the Krude Model
Ollama automatically serves the fine-tuned model on your RTX 3050 GPU:
```bash
ollama run Krude-risk
```
*(If Ollama is already running in your background/system tray, it is ready!)*

### Step 2: Start the FastAPI Backend & Dashboard
Run the launcher from the project root:
```bash
python run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`**

Interactive OpenAPI documentation is available at:
👉 **`http://127.0.0.1:8000/docs`**

---

## 📊 Data Formats & Schemas

All structured datasets are located in `backend/data/`:
* **`corridors.json`**: Maritime sea lanes, waypoints, transit days, normal/surge freight, and war insurance rates.
* **`refineries.json`**: Indian refineries (Jamnagar, Vadinar, Paradip, Kochi, Mangalore, Panipat, Mumbai, Vizag) with capacity, API ranges, max sulfur %, and inventory buffers.
* **`spr_facilities.json`**: Underground rock caverns (Mangalore, Padur, Vizag, Chandikhol) with capacities and pipeline connections.
* **`crude_grades.json`**: 13+ global crude benchmarks with API gravity, sulfur %, FOB differentials, and refinery compatibility scores.
* **`geopolitical_events.json`**: Live incident logs with severity scores and disruption probabilities.
* **`macro_parameters.json`**: India energy consumption (~5.4 MBPD), 88% import dependency, inflation sensitivity, and CAD multipliers.

---

## 🧠 Fine-Tuning Your Own Model & Adding It Later

### Step 1: Export Training Data
Click **"Export Fine-Tuning Dataset (.jsonl)"** in the UI **Fine-Tuning Hub** tab, or run:
```bash
python backend/training/generate_dataset.py
```
This generates `backend/models/oil_supply_chain_instruct_dataset.jsonl` formatted for instruction fine-tuning.

### Step 2: Fine-Tune with Unsloth / HuggingFace TRL
Use Google Colab or your GPU to train base `Llama-3-8B-Instruct` or `Mistral-7B` on the dataset. Detailed sample scripts are available in [`backend/training/fine_tuning_guide.md`](backend/training/fine_tuning_guide.md).

### Step 3: Hot-Swap into the Live System
* **Via Ollama**: Export your trained model to GGUF, run `ollama create oil-llama3 -f Modelfile`, and select **Ollama** in the web dashboard.
* **Via PyTorch**: Drop your `.safetensors` or `.bin` weights into `backend/models/` and select **CUSTOM_PYTORCH**.
* **Via vLLM / API**: Set your endpoint URL (e.g. `http://localhost:8000`) and select **API_ENDPOINT**.

The system instantly routes all scenario simulations and executive briefs through your custom model!

---

## 🧪 Automated Tests

Run the test suite:
```bash
python -m unittest backend/tests/test_engine.py
```
