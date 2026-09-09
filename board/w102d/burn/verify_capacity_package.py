#!/usr/bin/env python3
"""Legacy entry point for the universal image payload comparison."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[2]/'w103d/burn/verify_capacity_rebuild.py'), run_name='__main__')
