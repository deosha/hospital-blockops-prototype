# Simple Deployment Guide

## Easiest Option: Use Vercel (Recommended)

Vercel provides the **simplest** way to deploy both frontend and backend with zero configuration.

### Prerequisites
- GitHub account (already have repository at `deosha/hospital-blockops-prototype`)
- OpenAI API key

### Step 1: Deploy via Vercel Web Interface

1. **Go to** https://vercel.com
2. **Sign up** with your GitHub account
3. **Import Project**: Click "Add New..." → "Project"
4. **Select** `deosha/hospital-blockops-prototype` from GitHub
5. **Configure**:
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
6. **Environment Variables** - Add:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```
7. **Click "Deploy"**

That's it! Vercel will:
- Build and deploy your frontend automatically
- Provide a URL like `https://hospital-blockops-prototype.vercel.app`

### Step 2: Deploy Backend to Vercel

Vercel also supports Python serverless functions:

1. **Create** `vercel.json` in project root:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/app.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "frontend/dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/app.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/dist/$1"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai-api-key"
  }
}
```

2. **Push to GitHub**:
```bash
git add vercel.json
git commit -m "Add Vercel configuration"
git push origin main
```

3. Vercel will auto-deploy on every push!

### Result
- **Frontend**: `https://hospital-blockops-prototype.vercel.app`
- **Backend API**: `https://hospital-blockops-prototype.vercel.app/api/*`

---

## Alternative: Manual Step-by-Step

If you prefer manual deployment:

### Frontend to Netlify (Free)
```bash
cd frontend
npm run build
# Drag and drop `dist` folder to https://app.netlify.com/drop
```

### Backend to Railway (Free)
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `deosha/hospital-blockops-prototype`
4. Set root directory: `backend`
5. Add environment variable: `OPENAI_API_KEY`
6. Deploy!

---

## Cost Comparison

| Platform | Free Tier | Cost (if exceeded) |
|----------|-----------|-------------------|
| **Vercel** | 100GB bandwidth/month | $20/month |
| **Netlify** | 100GB bandwidth/month | $19/month |
| **Railway** | $5 credit/month | $0.000463/GB-hour |
| **Render** | 750 hours/month | $7/month |

**Recommended**: Vercel (easiest, both frontend + backend in one place)

---

## Next Steps

Once deployed:
1. Copy the live URL
2. Update the LaTeX paper with the URL
3. Test the demo thoroughly
4. Submit the paper!

**Need help?** Open an issue on GitHub: https://github.com/deosha/hospital-blockops-prototype/issues
