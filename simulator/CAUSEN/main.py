"""
CAUSEN AI: Root Entry Point
Delegates execution to causen_ai_simulation/main.py
"""
import sys
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent / "causen_ai_simulation"
sys.path.insert(0, str(SIM_DIR))

from main import main

if __name__ == "__main__":
    main()
