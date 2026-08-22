"""
Dataset Generation Script for Fine-Tuning Energy Security AI Models.
Run: python backend/training/generate_dataset.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from engine.fine_tuning_adapter import AIModelManager

def main():
    data_dir = backend_dir / "data"
    models_dir = backend_dir / "models"
    
    print("=" * 60)
    print("AI Energy Supply Chain: Generating Fine-Tuning Dataset")
    print("=" * 60)
    
    manager = AIModelManager(data_dir, models_dir)
    res = manager.export_fine_tuning_dataset()
    
    print(f"[+] Status: {res['status']}")
    print(f"[+] Samples Created: {res['samples_generated']}")
    print(f"[+] JSONL Path: {res['jsonl_path']}")
    print("=" * 60)
    print("Ready for fine-tuning on Unsloth, Hugging Face TRL, or Colab!")

if __name__ == "__main__":
    main()
