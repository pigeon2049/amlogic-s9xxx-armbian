#!/usr/bin/env python3
"""Legacy entry point for the unified W103D/W102D capacity regression suite."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[2]/'w103d/burn/test_bootstrap.py'), run_name='__main__')
