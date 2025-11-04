"""
WSGI Entry Point for Production Deployment
"""
from src.main import app

if __name__ == "__main__":
    app.run()

