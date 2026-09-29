"""Vercel Serverless Function Entrypoint for Bank Transaction Anomaly Flagger.

Exposes Bottle WSGI Application to Vercel's Python runtime.
"""

import os
import sys

# Ensure project root is on the Python module search path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the configured Bottle application
from web_app import app

# Vercel's @vercel/python builder automatically detects and wraps WSGI
# applications when `app` is exposed at module level.
