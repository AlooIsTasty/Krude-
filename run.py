"""
Krude | Energy Supply Chain & Geopolitical Risk Digital Twin
Entry point launcher.

Usage:
    python run.py
"""
import sys
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    print("=" * 70)
    print("  Krude: Energy Supply Chain & Geopolitical Risk Digital Twin")
    print("=" * 70)
    print("  * Starting FastAPI Server on http://127.0.0.1:8000")
    print("  * Serving Krude Dashboard at http://127.0.0.1:8000/")
    print("  * Interactive API Docs available at http://127.0.0.1:8000/docs")
    print("=" * 70)
    
    sys.path.insert(0, str(BASE_DIR))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
