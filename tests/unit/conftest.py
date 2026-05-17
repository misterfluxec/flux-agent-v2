# Minimal conftest for unit tests (no DB dependencies needed)
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
