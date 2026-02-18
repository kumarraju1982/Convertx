# 🚀 Prepare Your Code for Free Deployment

## Quick Preparation Steps

### 1. Ensure Git Repository is Ready

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit changes
git commit -m "Prepare for free deployment"

# Create GitHub repository and push
# Go to github.com and create a new repository
# Then run:
git remote add origin https://github.com/YOUR_USERNAME/convertx.git
git branch -M main
git push -u origin main
```

### 2. Files Already Prepared ✅

The following files have been created/updated for deployment:

- ✅ `backend/.env.example` - Environment variables template
- ✅ `frontend/.env.example` - Frontend environment template
- ✅ `frontend/.env.production` - Production environment config
- ✅ `render.yaml` - Render.com blueprint (optional)
- ✅ `backend/app/celery_app.py` - Updated for Redis Cloud password support
- ✅ `backend/app/config.py` - Updated for Redis Cloud
- ✅ `frontend/src/services/api.ts` - Updated for environment-based API URL
- ✅ `FREE_DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment guide

### 3. What You Need to Do

#### Option A: Manual Deployment (Recommended for First Time)
Follow the **FREE_DEPLOYMENT_CHECKLIST.md** file step by step.

#### Option B: Quick Deploy with Render Blueprint
1. Push code to GitHub
2. Go to Render.com
3. Click "New" → "Blueprint"
4. Connect your repository
5. Render will read `render.yaml` and create both services
6. Add Redis credentials manually in environment variables

### 4. Pre-Deployment Checklist

Before deploying, make sure:

- [ ] Code is pushed to GitHub
- [ ] All tests pass locally
- [ ] Redis Cloud account created
- [ ] Redis credentials ready (host, port, password)
- [ ] You have accounts on:
  - [ ] GitHub (for code hosting)
  - [ ] Render.com (for backend)
  - [ ] Vercel.com (for frontend)
  - [ ] Redis.com (for database)

### 5. Deployment Order

**IMPORTANT**: Deploy in this order:

1. **First**: Redis Cloud (database)
2. **Second**: Render Backend API
3. **Third**: Render Celery Worker
4. **Fourth**: Vercel Frontend
5. **Fifth**: Update CORS settings

### 6. Environment Variables You'll Need

#### For Render (Backend + Celery):
```
FLASK_ENV=production
PYTHON_VERSION=3.11.0
UPLOAD_FOLDER=/tmp/uploads
OCR_ENGINE=surya
REDIS_HOST=[from Redis Cloud]
REDIS_PORT=[from Redis Cloud]
REDIS_PASSWORD=[from Redis Cloud]
REDIS_DB=0
```

#### For Vercel (Frontend):
```
VITE_API_URL=https://your-backend.onrender.com/api
```

### 7. Testing Locally Before Deployment

```bash
# Test backend
cd backend
python -m pytest tests/ -v

# Test frontend
cd frontend
npm test

# Run locally to verify
# Terminal 1: Redis
redis-server

# Terminal 2: Celery
cd backend
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Backend API
cd backend
python -m flask run

# Terminal 4: Frontend
cd frontend
npm run dev
```

### 8. After Deployment

1. Visit your Vercel URL
2. Test with a small PDF (1-2 pages)
3. First request takes 30-60 seconds (normal for free tier)
4. Verify conversion works
5. Download and check Word document

### 9. Optional: Keep Services Awake

Use UptimeRobot (free) to ping your API every 14 minutes:
- URL to monitor: `https://your-backend.onrender.com/api/health`
- Interval: 14 minutes
- This prevents the 30-60 second wake-up time

### 10. Get Help

If you encounter issues:
1. Check Render logs (click service → Logs tab)
2. Check Vercel logs (Deployments → View logs)
3. Check Redis Cloud dashboard
4. Review FREE_DEPLOYMENT_CHECKLIST.md troubleshooting section

---

## 🎯 Ready to Deploy?

Open **FREE_DEPLOYMENT_CHECKLIST.md** and follow the step-by-step guide!

**Estimated Time**: 30 minutes total
**Cost**: $0/month forever
**Result**: Live, production-ready application!
