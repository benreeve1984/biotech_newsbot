import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our FastHTML app
from app import app

# This is what Vercel will use as the serverless function
def handler(request, response):
    return app(request, response) 