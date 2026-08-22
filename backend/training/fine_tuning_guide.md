# Fine-Tuning & Model Integration Guide

This guide explains how you can train a pre-trained open-source Large Language Model (e.g. **Llama-3-8B-Instruct**, **Mistral-7B**, **Qwen-2.5**, or **DeepSeek-R1-Distill**) on energy supply chain risk, and seamlessly plug it into this application.

---

## 1. How the Pluggable Architecture Works

The system decouples the **Analytical & Simulation Logic** from the **AI Intelligence Layer** via the `AIModelManager` adapter (`backend/engine/fine_tuning_adapter.py`).

```
[Web Dashboard / Digital Twin UI]
                │
                ▼ (REST API)
[FastAPI Simulation Server]
  ├── GeopoliticalRiskAgent
  ├── DisruptionScenarioModeller
  ├── AdaptiveProcurementOrchestrator
  ├── StrategicReserveOptimiser
  └── AIModelManager (Pluggable Model Adapter)
              │
    ┌─────────┼───────────────────────────┬──────────────────────────┐
    ▼         ▼                           ▼                          ▼
[Built-in]  [Ollama Local Engine]   [PyTorch / Transformers]    [vLLM / Cloud API]
 (Fast)      (e.g., Llama-3 GGUF)    (./backend/models/*.bin)    (OpenAI format)
```

---

## 2. Step-by-Step Fine-Tuning Workflow

### Step 1: Export Training Data from this App
You can export instruction-tuning data anytime via the Web UI's **Fine-Tuning Hub** or by running:
```bash
python backend/training/generate_dataset.py
```
This produces `backend/models/oil_supply_chain_instruct_dataset.jsonl` in the standard format:
```json
{
  "instruction": "You are India's Strategic Energy Security AI. Analyze the geopolitical disruption scenario...",
  "input": "Scenario: Strait of Hormuz 80% Blockade...",
  "output": "1. Divert 600k bpd to West Africa (Bonny Light). 2. Draw 250k bpd from Mangalore SPR..."
}
```

### Step 2: Fine-Tune with LoRA / QLoRA
You can use **Unsloth** (recommended for speed and low VRAM) or **Hugging Face TRL** on Google Colab or a local GPU (RTX 3060/4090 or A100):

```python
# Example Unsloth / Hugging Face Colab Script
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Load Pretrained Base Model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
)

# 2. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
)

# 3. Train on our exported dataset
dataset = load_dataset("json", data_files="oil_supply_chain_instruct_dataset.jsonl")
trainer = SFTTrainer(
    model = model,
    train_dataset = dataset["train"],
    dataset_text_field = "text",
    max_seq_length = 2048,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60,
        learning_rate = 2e-4,
        fp16 = True,
        output_dir = "outputs",
    ),
)
trainer.train()

# 4. Save and Export to GGUF (for Ollama) or HuggingFace
model.save_pretrained_gguf("custom_oil_llama3", tokenizer, quantization_method = "q4_k_m")
```

---

## 3. How to Plug It In Afterwards (3 Easy Options)

### Option A: Using Ollama (Easiest & Fastest Local Serving)
1. Install [Ollama](https://ollama.com).
2. Create a `Modelfile`:
   ```dockerfile
   FROM ./custom_oil_llama3.gguf
   SYSTEM "You are India's Chief Energy Security & Crude Logistics AI Strategist."
   ```
3. Register your model in Ollama:
   ```bash
   ollama create oil-llama3 -f Modelfile
   ollama run oil-llama3
   ```
4. In the Web UI **Fine-Tuning Hub** (or via API), switch backend to:
   - **Backend**: `Ollama Local LLM`
   - **Model Name**: `oil-llama3`
   - **Endpoint**: `http://localhost:11434`

### Option B: Drop Weights directly into `./backend/models/`
Drop your merged weights or adapter weights into `./backend/models/` and select `CUSTOM_PYTORCH`.

### Option C: Using vLLM or OpenAI-Compatible Cloud Endpoint
Run your model on a remote GPU server with vLLM:
```bash
python -m vllm.entrypoints.openai.api_server --model my-oil-model --port 8000
```
In the app UI, set backend to `Cloud / vLLM API` with URL `http://localhost:8000`.

---

## 4. Verification & Testing
Once connected, every time you run a disruption scenario in the Digital Twin, the app will feed the live numbers to your fine-tuned model and display its generated strategic reasoning directly on the executive brief dashboard!
