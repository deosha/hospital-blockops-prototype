# AWS Deployment Guide for Hospital BlockOps Demo

## Architecture Overview

**Stack:**
- **Backend:** Python Flask API (port 5000)
- **Frontend:** React + TypeScript + Vite (static build)
- **Dependencies:** OpenAI API (requires API key)

---

## Recommended AWS Deployment Options

### **Option 1: AWS Elastic Beanstalk (Easiest) ⭐ RECOMMENDED**

**Best for:** Quick deployment, automatic scaling, minimal DevOps

#### Architecture
```
CloudFront (CDN)
    ↓
S3 (Static Frontend)
    ↓
Elastic Beanstalk (Python Flask Backend)
    ↓
Secrets Manager (OpenAI API Key)
```

#### Deployment Steps

**1. Backend Deployment (Elastic Beanstalk)**

```bash
cd hospital-blockops-demo/backend

# Create .ebextensions config
mkdir -p .ebextensions
cat > .ebextensions/python.config << 'EOF'
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    FLASK_PORT: "8000"
    FLASK_DEBUG: "False"
    CORS_ORIGINS: "https://your-cloudfront-domain.cloudfront.net"
EOF

# Create application.py (EB expects this name)
cat > application.py << 'EOF'
from app import app as application

if __name__ == "__main__":
    application.run()
EOF

# Initialize EB
eb init -p python-3.11 hospital-blockops --region us-east-1

# Create environment
eb create hospital-blockops-prod --single

# Set OpenAI API key via environment variable
eb setenv OPENAI_API_KEY=sk-your-key-here

# Deploy
eb deploy
```

**2. Frontend Deployment (S3 + CloudFront)**

```bash
cd hospital-blockops-demo/frontend

# Update API endpoint in src/config.ts or .env
echo "VITE_API_BASE_URL=https://your-eb-url.elasticbeanstalk.com/api" > .env.production

# Build
npm run build

# Create S3 bucket
aws s3 mb s3://hospital-blockops-demo-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://hospital-blockops-demo-frontend \
  --index-document index.html \
  --error-document index.html

# Upload build
aws s3 sync dist/ s3://hospital-blockops-demo-frontend --delete

# Create CloudFront distribution (via AWS Console or CLI)
aws cloudfront create-distribution \
  --origin-domain-name hospital-blockops-demo-frontend.s3.amazonaws.com \
  --default-root-object index.html
```

**Cost Estimate:** $15-30/month (with free tier)

---

### **Option 2: AWS Amplify (Fastest) 🚀**

**Best for:** Fastest deployment, CI/CD integration, zero config

#### Deployment Steps

```bash
cd hospital-blockops-demo

# Install Amplify CLI
npm install -g @aws-amplify/cli
amplify configure

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting
# Select: Amazon CloudFront and S3

# Add API (creates Lambda + API Gateway automatically)
amplify add api
# Select: REST
# Select: Create new Lambda function
# Template: Serverless Express function

# Copy backend code to Lambda
cp -r backend/* amplify/backend/function/hospitalblockopsapi/src/

# Update package.json in Lambda
cd amplify/backend/function/hospitalblockopsapi/src
npm init -y
npm install flask serverless-wsgi

# Deploy everything
amplify push

# Publish
amplify publish
```

**Cost Estimate:** $10-25/month (with free tier)

---

### **Option 3: Docker + ECS Fargate (Production-Ready) 🐳**

**Best for:** Full control, scalability, container-based

#### Architecture
```
ALB (Load Balancer)
    ↓
ECS Fargate Tasks
    ├── Backend Container (Flask)
    └── Frontend Container (Nginx)
```

#### Deployment Files

**1. Create Dockerfile for Backend**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

**2. Create Dockerfile for Frontend**

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

**3. Create nginx.conf**

```nginx
# frontend/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**4. Create docker-compose.yml (for testing locally)**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FLASK_DEBUG=False
      - CORS_ORIGINS=http://localhost:3000
    env_file:
      - ./backend/.env

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

**5. Deploy to ECS**

```bash
# Build and push to ECR
aws ecr create-repository --repository-name hospital-blockops-backend
aws ecr create-repository --repository-name hospital-blockops-frontend

# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
cd backend
docker build -t hospital-blockops-backend .
docker tag hospital-blockops-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/hospital-blockops-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/hospital-blockops-backend:latest

# Build and push frontend
cd ../frontend
docker build -t hospital-blockops-frontend .
docker tag hospital-blockops-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/hospital-blockops-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/hospital-blockops-frontend:latest

# Create ECS cluster (via AWS Console or Terraform)
# Create Task Definition with both containers
# Create Service with ALB
```

**Cost Estimate:** $50-100/month (0.25 vCPU, 0.5GB RAM per task)

---

### **Option 4: Serverless (AWS Lambda + API Gateway + S3) ⚡**

**Best for:** Low traffic, minimal cost, pay-per-use

#### Deployment with Zappa

```bash
cd backend

# Install Zappa
pip install zappa

# Initialize Zappa
zappa init

# Edit zappa_settings.json
cat > zappa_settings.json << 'EOF'
{
    "production": {
        "app_function": "app.app",
        "aws_region": "us-east-1",
        "profile_name": "default",
        "project_name": "hospital-blockops",
        "runtime": "python3.11",
        "s3_bucket": "hospital-blockops-zappa",
        "environment_variables": {
            "FLASK_DEBUG": "False"
        },
        "aws_environment_variables": {
            "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:xxx:secret:openai-key"
        }
    }
}
EOF

# Deploy
zappa deploy production

# Update
zappa update production

# Get URL
zappa status production
```

**Frontend:** Same as Option 1 (S3 + CloudFront)

**Cost Estimate:** $5-15/month (very low traffic)

---

## Recommended Deployment: Option 1 (Elastic Beanstalk + S3)

### Quick Start Script

```bash
#!/bin/bash
# deploy-aws.sh

set -e

echo "🚀 Deploying Hospital BlockOps to AWS..."

# 1. Deploy Backend to Elastic Beanstalk
echo "📦 Deploying Backend..."
cd backend
eb init -p python-3.11 hospital-blockops --region us-east-1
eb create hospital-blockops-prod --single
eb setenv OPENAI_API_KEY=$OPENAI_API_KEY FLASK_DEBUG=False
EB_URL=$(eb status | grep "CNAME" | awk '{print $2}')
echo "✅ Backend deployed to: https://$EB_URL"

# 2. Build and Deploy Frontend to S3
echo "🎨 Building Frontend..."
cd ../frontend
echo "VITE_API_BASE_URL=https://$EB_URL/api" > .env.production
npm run build

echo "☁️ Deploying Frontend to S3..."
aws s3 mb s3://hospital-blockops-demo --region us-east-1
aws s3 sync dist/ s3://hospital-blockops-demo --delete
aws s3 website s3://hospital-blockops-demo \
  --index-document index.html \
  --error-document index.html

# 3. Create CloudFront distribution
echo "🌐 Creating CloudFront distribution..."
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
  --origin-domain-name hospital-blockops-demo.s3-website-us-east-1.amazonaws.com \
  --default-root-object index.html \
  --query 'Distribution.Id' --output text)

CLOUDFRONT_URL=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID \
  --query 'Distribution.DomainName' --output text)

echo "✅ Frontend deployed to: https://$CLOUDFRONT_URL"

# 4. Update CORS in backend
echo "🔧 Updating CORS settings..."
cd ../backend
eb setenv CORS_ORIGINS=https://$CLOUDFRONT_URL

echo "🎉 Deployment Complete!"
echo "📊 Demo URL: https://$CLOUDFRONT_URL"
echo "🔗 API URL: https://$EB_URL"
```

---

## Environment Variables

### Backend (.env)
```bash
OPENAI_API_KEY=sk-your-openai-api-key
FLASK_PORT=5000
FLASK_DEBUG=False
CORS_ORIGINS=https://your-cloudfront-domain.cloudfront.net
```

### Frontend (.env.production)
```bash
VITE_API_BASE_URL=https://your-backend-url.elasticbeanstalk.com/api
```

---

## Security Considerations

1. **API Key Management**
   - Store OpenAI API key in AWS Secrets Manager
   - Reference in EB environment: `arn:aws:secretsmanager:region:account:secret:name`

2. **CORS Configuration**
   - Restrict CORS to your CloudFront domain only
   - Update `CORS_ORIGINS` environment variable

3. **HTTPS**
   - CloudFront provides free SSL certificates
   - Configure custom domain with Route 53 + ACM certificate

4. **IAM Roles**
   - EB instance role needs Secrets Manager read access
   - Minimal permissions following least privilege

---

## Monitoring & Logs

```bash
# View EB logs
eb logs

# CloudWatch logs
aws logs tail /aws/elasticbeanstalk/hospital-blockops-prod/var/log/web.stdout.log --follow

# S3 CloudFront logs
aws s3 sync s3://hospital-blockops-demo-logs/ ./logs/
```

---

## Cost Breakdown (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| Elastic Beanstalk | t3.micro (1 instance) | $8-10 |
| S3 | Static hosting (1GB storage) | $0.50 |
| CloudFront | 10GB transfer | $1-2 |
| Route 53 | Hosted zone + DNS | $0.50 |
| OpenAI API | ~10K requests/month | $5-10 |
| **Total** | | **$15-25/month** |

*Free tier eligible for first 12 months*

---

## Troubleshooting

### Backend Issues
```bash
# Check EB health
eb health

# SSH into instance
eb ssh

# View real-time logs
eb logs --stream
```

### Frontend Issues
```bash
# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

# Check S3 bucket policy
aws s3api get-bucket-policy --bucket hospital-blockops-demo
```

### CORS Errors
- Verify `CORS_ORIGINS` environment variable in EB
- Check CloudFront domain matches CORS whitelist
- Clear browser cache

---

## CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy Backend
        run: |
          cd backend
          eb deploy hospital-blockops-prod

      - name: Deploy Frontend
        run: |
          cd frontend
          npm ci
          npm run build
          aws s3 sync dist/ s3://hospital-blockops-demo --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CLOUDFRONT_DIST_ID }} --paths "/*"
```

---

## Next Steps

1. **Domain Setup**
   - Register domain in Route 53
   - Request SSL certificate in ACM
   - Configure CloudFront with custom domain

2. **Monitoring**
   - Enable CloudWatch alarms for API errors
   - Set up SNS notifications for downtime
   - Configure AWS X-Ray for request tracing

3. **Scaling**
   - Enable EB auto-scaling (2-4 instances)
   - Configure ALB health checks
   - Set up RDS for persistent blockchain storage (future)

---

**Demo URL After Deployment:** Will be provided in format:
- Frontend: `https://dxxxxx.cloudfront.net`
- Backend API: `https://hospital-blockops-prod.elasticbeanstalk.com`

**Total Setup Time:** 15-30 minutes
