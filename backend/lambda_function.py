"""
AWS Lambda handler for Hospital BlockOps Flask backend
Wraps Flask app using Mangum for Lambda compatibility
"""

import os
import sys

# Ensure all modules can be imported
sys.path.insert(0, os.path.dirname(__file__))

from mangum import Mangum
from app import app

# Set production defaults
os.environ.setdefault('FLASK_DEBUG', 'False')

# Lambda handler - Mangum converts API Gateway events to ASGI/WSGI
handler = Mangum(app, lifespan="off", api_gateway_base_path="/prod")

# For testing locally
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
