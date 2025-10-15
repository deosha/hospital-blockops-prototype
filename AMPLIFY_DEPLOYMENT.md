# AWS Amplify Deployment Guide

Complete guide to deploy Hospital BlockOps to AWS Amplify.

---

## Overview

AWS Amplify provides the **fastest** deployment option for this demo:
- **Frontend**: Automatically built and hosted on CloudFront CDN
- **Backend**: Deploy as Lambda function via API Gateway
- **Cost**: ~$10-20/month (free tier eligible)
- **Setup Time**: 10-15 minutes

---

## Prerequisites

1. **AWS Account** with Amplify access
2. **GitHub Repository** (already created at `deosha/hospital-blockops-prototype`)
3. **OpenAI API Key** (for LLM agents)
4. **Node.js 18+** and **Python 3.11+** installed locally

---

## Option 1: Deploy via Amplify Console (Easiest) ⭐

### Step 1: Connect GitHub Repository

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click **"New app"** → **"Host web app"**
3. Select **GitHub** as the repository service
4. Authorize AWS Amplify to access your GitHub account
5. Select repository: `deosha/hospital-blockops-prototype`
6. Select branch: `main`

### Step 2: Configure Build Settings

Amplify will auto-detect the `amplify.yml` file. Verify it shows:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

### Step 3: Add Environment Variables

In the Amplify Console, add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `VITE_API_BASE_URL` | (will be set after backend deployment) | Frontend API endpoint |

### Step 4: Deploy Frontend

Click **"Save and deploy"**

Amplify will:
1. Clone your repository
2. Install dependencies (`npm ci`)
3. Build the frontend (`npm run build`)
4. Deploy to CloudFront CDN

**Result**: Your frontend will be live at `https://main.xxxxxx.amplifyapp.com`

---

## Option 2: Deploy Backend with Amplify Functions

### Step 1: Initialize Amplify CLI

```bash
cd /Users/deo/ai_in_hospital/hospital-blockops-demo

# Install Amplify CLI globally
npm install -g @aws-amplify/cli

# Configure Amplify CLI with your AWS credentials
amplify configure
```

Follow prompts:
- Region: `us-east-1` (or your preferred region)
- IAM User: Create new user with **AdministratorAccess-Amplify**

### Step 2: Initialize Amplify Project

```bash
# Initialize new Amplify project
amplify init

# Answer prompts:
# - Project name: hospitalblockops
# - Environment: prod
# - Default editor: (your choice)
# - App type: javascript
# - Framework: react
# - Source directory: frontend/src
# - Distribution directory: frontend/dist
# - Build command: npm run build
# - Start command: npm run dev
```

### Step 3: Add API with Lambda Function

```bash
# Add REST API with Lambda backend
amplify add api

# Answer prompts:
# - Select service type: REST
# - Provide friendly name: hospitalblockopsapi
# - Provide path: /api
# - Lambda source: Create new Lambda function
# - Function name: hospitalblockopsBackend
# - Runtime: Python
# - Template: Serverless ExpressJS function (Amplify will convert)
# - Advanced settings: Yes
# - Access other resources: No
# - Environment variables: Yes
#   - OPENAI_API_KEY: your-openai-key-here
# - Configure CORS: Yes
# - Add another path: No
```

### Step 4: Convert Flask App to Lambda

Create Lambda handler wrapper:

```bash
cd amplify/backend/function/hospitalblockopsBackend/src
```

Create `lambda_handler.py`:

```python
import json
import sys
import os

# Add parent directory to path to import Flask app
sys.path.insert(0, os.path.dirname(__file__))

from app import app

def handler(event, context):
    """AWS Lambda handler for Flask app"""

    # Convert API Gateway event to Flask request
    from werkzeug.wrappers import Request, Response
    from io import BytesIO

    # Build WSGI environ from Lambda event
    environ = {
        'REQUEST_METHOD': event['httpMethod'],
        'SCRIPT_NAME': '',
        'PATH_INFO': event['path'],
        'QUERY_STRING': event.get('queryStringParameters', ''),
        'CONTENT_TYPE': event['headers'].get('Content-Type', ''),
        'CONTENT_LENGTH': len(event.get('body', '')),
        'SERVER_NAME': 'lambda',
        'SERVER_PORT': '80',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(event.get('body', '').encode('utf-8')),
        'wsgi.errors': sys.stderr,
        'wsgi.multiprocess': False,
        'wsgi.multithread': False,
        'wsgi.run_once': False,
    }

    # Add headers to environ
    for key, value in event.get('headers', {}).items():
        key = 'HTTP_' + key.upper().replace('-', '_')
        environ[key] = value

    # Run Flask app
    response = Response.from_app(app, environ)

    # Convert Flask response to API Gateway format
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }
```

Copy backend files:

```bash
# Copy all backend files to Lambda function
cp -r ../../../../../backend/* .
```

Update `requirements.txt` for Lambda:

```txt
flask==3.0.0
flask-cors==4.0.0
openai>=1.50.0
python-dotenv==1.0.0
requests==2.31.0
pydantic>=2.8.0
mangum==0.17.0
```

### Step 5: Deploy Backend

```bash
cd /Users/deo/ai_in_hospital/hospital-blockops-demo

# Deploy API and Lambda
amplify push

# This will:
# 1. Create API Gateway REST API
# 2. Deploy Lambda function with your Flask backend
# 3. Configure CORS
# 4. Set up CloudWatch logs
```

### Step 6: Get API Endpoint

```bash
# Get the API endpoint URL
amplify status

# Output will show:
# API endpoint: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
```

### Step 7: Update Frontend Environment Variable

```bash
# In Amplify Console, update environment variable:
VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/api
```

Or create `.env.production` locally:

```bash
cd frontend
echo "VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/api" > .env.production
```

### Step 8: Commit and Push

```bash
git add amplify.yml .env.production
git commit -m "Add Amplify deployment configuration"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_personal" git push origin main
```

Amplify will automatically trigger a new build and deployment.

---

## Option 3: Simplified Backend - API Gateway + Lambda (Recommended)

For a simpler deployment, use AWS Lambda Web Adapter or Mangum to wrap Flask:

### Using Mangum (ASGI to Lambda)

```bash
cd backend

# Install mangum
pip install mangum

# Create lambda_function.py
cat > lambda_function.py << 'EOF'
from mangum import Mangum
from app import app

# Wrap Flask app with Mangum for Lambda
handler = Mangum(app, lifespan="off")
EOF

# Create deployment package
pip install -r requirements.txt -t package/
cp -r * package/
cd package
zip -r ../function.zip .
cd ..

# Upload to Lambda via AWS CLI
aws lambda create-function \
  --function-name hospital-blockops-backend \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda_function.handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{OPENAI_API_KEY=sk-your-key-here,FLASK_DEBUG=False}"

# Create API Gateway
aws apigatewayv2 create-api \
  --name hospital-blockops-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:hospital-blockops-backend
```

---

## Complete Manual Deployment Steps

If you prefer full control:

### 1. Deploy Frontend to Amplify Hosting

```bash
cd frontend

# Build frontend
npm run build

# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize hosting
amplify init
amplify add hosting

# Select:
# - Hosting with Amplify Console
# - Manual deployment

# Publish
amplify publish
```

### 2. Deploy Backend to Lambda (Manual)

```bash
cd backend

# Create virtual environment
python -m venv lambda_env
source lambda_env/bin/activate

# Install dependencies in a package directory
pip install -r requirements.txt -t lambda_package/

# Copy application code
cp -r agents api blockchain evaluation *.py lambda_package/

# Create Lambda handler
cat > lambda_package/lambda_function.py << 'EOF'
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app import app
from mangum import Mangum

handler = Mangum(app, lifespan="off")
EOF

# Create ZIP
cd lambda_package
zip -r ../backend-deployment.zip .
cd ..

# Upload via AWS Console or CLI
aws lambda create-function \
  --function-name hospital-blockops-api \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --handler lambda_function.handler \
  --zip-file fileb://backend-deployment.zip \
  --timeout 60 \
  --memory-size 1024 \
  --environment Variables="{OPENAI_API_KEY=$OPENAI_API_KEY,FLASK_DEBUG=False,CORS_ORIGINS=https://your-amplify-url.amplifyapp.com}"
```

### 3. Create API Gateway

```bash
# Create HTTP API
API_ID=$(aws apigatewayv2 create-api \
  --name hospital-blockops \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:ACCOUNT_ID:function:hospital-blockops-api \
  --query 'ApiId' --output text)

# Get API endpoint
echo "API Endpoint: https://$API_ID.execute-api.us-east-1.amazonaws.com"
```

### 4. Configure CORS

```bash
# Add CORS configuration to API Gateway
aws apigatewayv2 update-api \
  --api-id $API_ID \
  --cors-configuration AllowOrigins="https://main.*.amplifyapp.com",AllowMethods="GET,POST,PUT,DELETE,OPTIONS",AllowHeaders="Content-Type,Authorization"
```

---

## Environment Variables

Set these in Amplify Console or Lambda:

### Frontend (Amplify Console → Environment Variables)
```bash
VITE_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/api
```

### Backend (Lambda Configuration → Environment Variables)
```bash
OPENAI_API_KEY=sk-your-openai-api-key
FLASK_DEBUG=False
CORS_ORIGINS=https://main.xxxxx.amplifyapp.com
```

---

## Continuous Deployment

Once connected to GitHub, Amplify will automatically:
1. Detect pushes to `main` branch
2. Build and deploy frontend
3. Update backend if changes detected
4. Invalidate CDN cache

### Branch Deployments

Create separate environments for dev/staging:

```bash
# Create staging branch
git checkout -b staging
git push origin staging

# In Amplify Console, connect staging branch
# It will deploy to: https://staging.xxxxx.amplifyapp.com
```

---

## Monitoring & Logs

### Frontend Logs
```bash
# View build logs in Amplify Console
# Or via CLI:
amplify console
```

### Backend Logs
```bash
# View Lambda logs in CloudWatch
aws logs tail /aws/lambda/hospital-blockops-api --follow

# Or via Amplify CLI:
amplify function logs hospitalblockopsBackend
```

---

## Cost Breakdown

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Amplify Hosting | 5GB storage, 15GB transfer | $0.50 |
| CloudFront | 10GB data transfer | $1.00 |
| Lambda | 100K requests, 512MB, 5s avg | $1.00 |
| API Gateway | 100K requests | $0.35 |
| CloudWatch Logs | 1GB logs | $0.50 |
| OpenAI API | ~10K requests | $5-10 |
| **Total** | | **$8-13/month** |

**Free Tier (12 months):**
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- CloudWatch: 5GB logs free

---

## Troubleshooting

### Frontend Build Fails
```bash
# Check Node version in amplify.yml
frontend:
  phases:
    preBuild:
      commands:
        - nvm install 18
        - nvm use 18
        - cd frontend
        - npm ci
```

### Backend Lambda Timeout
- Increase timeout: Lambda → Configuration → Timeout → 60 seconds
- Increase memory: Lambda → Configuration → Memory → 1024 MB

### CORS Errors
- Verify `CORS_ORIGINS` in Lambda environment variables
- Check API Gateway CORS configuration
- Ensure frontend URL matches exactly (with https://)

### OpenAI API Errors
- Verify `OPENAI_API_KEY` is set in Lambda
- Check CloudWatch logs for specific error messages
- Ensure Lambda has internet access (VPC configuration if needed)

---

## Manual Deployment Script

```bash
#!/bin/bash
# deploy-amplify.sh

set -e

echo "🚀 Deploying Hospital BlockOps to AWS Amplify..."

# 1. Install dependencies
npm install -g @aws-amplify/cli

# 2. Configure Amplify
echo "📝 Configuring Amplify..."
amplify configure

# 3. Initialize project
echo "🔧 Initializing Amplify project..."
amplify init --app https://github.com/deosha/hospital-blockops-prototype \
  --name hospitalblockops \
  --envName prod \
  --defaultEditor code \
  --yes

# 4. Add API
echo "🌐 Adding REST API..."
amplify add api

# 5. Add hosting
echo "☁️ Adding hosting..."
amplify add hosting

# 6. Deploy
echo "🚀 Deploying..."
amplify push --yes

# 7. Publish
echo "📦 Publishing..."
amplify publish --yes

# 8. Get URLs
echo "✅ Deployment complete!"
amplify status
```

---

## Next Steps After Deployment

1. **Update Paper URLs**: Replace placeholders in LaTeX paper:
   - Live Demo: `https://main.xxxxx.amplifyapp.com`
   - GitHub: `https://github.com/deosha/hospital-blockops-prototype`

2. **Custom Domain** (Optional):
   ```bash
   amplify add domain
   # Follow prompts to add custom domain
   ```

3. **Add Monitoring**:
   - Enable AWS X-Ray for Lambda tracing
   - Set up CloudWatch alarms for errors
   - Configure SNS notifications

4. **Security Hardening**:
   - Rotate OpenAI API key regularly
   - Enable AWS WAF on API Gateway
   - Implement rate limiting

---

## Quick Reference

```bash
# View app status
amplify status

# View console
amplify console

# View logs
amplify function logs hospitalblockopsBackend

# Update function
amplify update function

# Delete app
amplify delete
```

---

**Total Setup Time**: 10-15 minutes
**Deployment URL**: Will be provided in format `https://main.dxxxxxxx.amplifyapp.com`
