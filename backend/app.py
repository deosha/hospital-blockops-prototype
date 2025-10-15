from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Import and register routes (blockchain-enabled version)
from api.routes_with_blockchain import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return {
        "service": "Hospital BlockOps API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "agents": "/api/agents",
            "blockchain": "/api/blockchain",
            "scenarios": "/api/scenario/run"
        }
    }

@app.route('/health')
def health_check():
    return {"status": "healthy", "message": "BlockOps backend is running"}

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print(f"🏥 Starting BlockOps Backend on port {port}")
    print(f"📊 Debug mode: {debug}")
    print(f"🔗 CORS enabled for: {os.getenv('CORS_ORIGINS', 'http://localhost:3000')}")

    # Initialize blockchain on startup
    from blockchain.manager import get_blockchain
    blockchain = get_blockchain()
    print(f"⛓️  Blockchain initialized with {len(blockchain.chain)} blocks")
    print(f"🔐 Genesis hash: {blockchain.chain[0].hash[:16]}...")

    # Initialize coordination engine to check mode
    from api.real_coordination import get_coordination_engine
    engine = get_coordination_engine()
    if engine.use_real_agents:
        print(f"🤖 Coordination Mode: REAL LLM AGENTS (OpenAI-powered)")
    else:
        print(f"🎭 Coordination Mode: DEMO SIMULATION (instant fallback)")

    app.run(host='0.0.0.0', port=port, debug=debug)
