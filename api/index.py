"""
Vercel Serverless Function Entry Point
"""
import sys
import os

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app

# Vercel expects the app to be available as a module-level variable
# This is the entry point for Vercel's serverless functions

