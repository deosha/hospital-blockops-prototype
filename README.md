# Hospital BlockOps - Multi-Agent Operations Prototype

**Autonomous Multi-Agent System for Hospital Non-Clinical Operations with Blockchain Trust Infrastructure**

![System Architecture](https://img.shields.io/badge/Status-Prototype-orange) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![React](https://img.shields.io/badge/React-18-61DAFB) ![License](https://img.shields.io/badge/License-MIT-green)

## Overview

Hospital BlockOps is a proof-of-concept demonstrating autonomous multi-agent coordination for hospital operations management. The system uses LLM-powered agents with blockchain-based audit trails to coordinate supply chain, financial, and facility decisions.

### Key Features

- **3 Operational Agents**: Supply Chain, Financial, Facility (real LLM integration)
- **8-Step Coordination Protocol**: FIPA-ACL inspired negotiation
- **Blockchain Audit Trail**: Simulated in-memory ledger with cryptographic verification
- **Graduated Autonomy**: Risk-based decision levels (automatic, approval-required, human-guided)
- **Interactive Dashboard**: Real-time agent status and coordination visualization
- **Explainable Decisions**: Natural language justifications for all agent actions

## Architecture

```
┌─────────────────┐
│  React Frontend │  Interactive Dashboard
└────────┬────────┘
         │
    ┌────▼────┐
    │  Flask  │  Coordination Engine
    │   API   │
    └────┬────┘
         │
    ┌────▼────────────────────────┐
    │  Multi-Agent System         │
    ├─────────────────────────────┤
    │  • Supply Chain Agent       │
    │  • Financial Agent          │
    │  • Facility Agent           │
    │  • Decision Support (LLM)   │
    └────┬────────────────────────┘
         │
    ┌────▼────────────────────────┐
    │  Simulated Blockchain       │
    │  (In-Memory Ledger)         │
    └─────────────────────────────┘
```

## Tech Stack

### Backend
- **Python 3.11** - Flask REST API
- **OpenAI API** - GPT-4 for agent reasoning
- **Pydantic** - Data validation
- **CORS** - Cross-origin support

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Recharts** - Data visualization

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOL
OPENAI_API_KEY=sk-your-openai-api-key-here
FLASK_PORT=5000
FLASK_DEBUG=True
CORS_ORIGINS=http://localhost:3000
EOL

# Run backend
python app.py
```

Backend will start on `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

Frontend will start on `http://localhost:3000`

## Demo Scenarios

### Scenario 1: Supply Chain Coordination
- **Trigger**: Low inventory detected (200 units, need 1,000)
- **Coordination**: Supply Chain → Financial (budget check) → Facility (storage check)
- **Result**: Order 800 units at $160/unit ($128K total, within constraints)

### Scenario 2: Budget Constraint Handling
- **Trigger**: Large order request exceeds monthly budget
- **Coordination**: Financial Agent rejects → Supply Chain proposes smaller order
- **Result**: Graduated approach with approval escalation

### Scenario 3: Storage Capacity Optimization
- **Trigger**: Multiple simultaneous orders
- **Coordination**: Facility Agent allocates storage → Supply Chain prioritizes
- **Result**: Space-optimized ordering sequence

## API Endpoints

```
GET  /api/health              - System health check
GET  /api/agents              - List all agents and status
GET  /api/blockchain          - View blockchain state
POST /api/scenario/run        - Execute coordination scenario
GET  /api/coordination/history - View past coordination events
```

## Project Structure

```
hospital-blockops-demo/
├── backend/
│   ├── agents/              # Agent implementations
│   │   ├── base.py          # Base agent class
│   │   ├── supply_chain.py  # Supply chain agent
│   │   ├── financial.py     # Financial agent
│   │   └── facility.py      # Facility agent
│   ├── api/                 # API routes
│   │   ├── routes_with_blockchain.py
│   │   └── real_coordination.py
│   ├── blockchain/          # Blockchain implementation
│   │   ├── block.py
│   │   └── manager.py
│   ├── evaluation/          # Monte Carlo simulation
│   │   └── monte_carlo_realistic.py
│   ├── app.py              # Flask app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── App.tsx         # Main app
│   ├── package.json
│   └── vite.config.ts
└── AWS_DEPLOYMENT.md       # AWS deployment guide
```

## Evaluation Methodology

The system includes a Monte Carlo simulation (1,000 runs × 365 days) parameterized with real hospital industry data:

- **Premier Healthcare Survey 2024**: 25% supply chain waste baseline
- **AHA 2024 Costs of Caring**: 56% labor cost share
- **Utah Drug Info Service 2023**: 99% facilities experience stockouts
- **HFMA Best Practices**: Supply chain benchmarks

**Note**: Demo uses scenario parameters as illustrative targets. Full validation requires deployment studies.

## Deployment

See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for complete AWS deployment instructions.

**Quick Deploy to AWS:**
```bash
# Option 1: Elastic Beanstalk (Recommended)
cd backend
eb init -p python-3.11 hospital-blockops
eb create hospital-blockops-prod
eb setenv OPENAI_API_KEY=your-key

# Option 2: Docker
docker-compose up -d
```

## Research Paper

This prototype accompanies the research paper:
**"Autonomous Multi-Agent Systems for Hospital Non-Clinical Operations: A Blockchain-Enabled Framework with Trustless Coordination"**

Submitted to: MLBSS-DEC25 Workshop (Machine Learning & Blockchain in Smart Systems)

## Implementation Status

✅ **Implemented**
- 3 of 5 agents (Supply Chain, Financial, Facility)
- OpenAI GPT API integration
- 8-step FIPA-ACL coordination protocol
- Simulated blockchain audit trail
- Interactive dashboard
- Graduated autonomy framework

🚧 **Planned (Future Work)**
- Energy Management Agent
- Scheduling Agent
- RAG system (vector database for hospital policies)
- LSTM forecasting models
- Deep RL coordination
- Real Hyperledger Fabric deployment
- HIS system integration

## Cost Estimates

### Development/Demo
- **OpenAI API**: ~$5-10/month (100-200 coordination events)
- **AWS Hosting**: $15-25/month (Elastic Beanstalk + S3 + CloudFront)

### Production Deployment (500-bed hospital)
- **Implementation**: $800K-1.2M (12-18 months)
- **Operating Cost**: $50K-100K/year
- **Projected ROI**: 6-18 months (based on 15-30% waste reduction)

## License

MIT License - See LICENSE file for details

## Citation

If you use this prototype in your research, please cite:

```bibtex
@inproceedings{hospitalblockops2025,
  title={Autonomous Multi-Agent Systems for Hospital Non-Clinical Operations: A Blockchain-Enabled Framework with Trustless Coordination},
  author={[Author Names]},
  booktitle={MLBSS-DEC25 Workshop},
  year={2025}
}
```

## Contact

- **Live Demo**: [URL-TO-BE-PROVIDED]
- **GitHub**: https://github.com/deosha/hospital-blockops-prototype
- **Issues**: Report bugs or request features via GitHub Issues

## Acknowledgments

Built with:
- OpenAI GPT-4 for agent reasoning
- React + TypeScript for frontend
- Flask for backend API
- TailwindCSS for styling

---

**⚠️ Research Prototype**: This is a proof-of-concept for academic research. Not intended for production medical use without extensive validation, regulatory approval, and safety testing.
