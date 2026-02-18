# 🚀 Free Deployment Checklist for ConvertX

Follow these steps to deploy your ConvertX application completely free!

## ✅ Prerequisites

- [ ] GitHub account (free)
- [ ] Git installed on your computer
- [ ] Your code pushed to a GitHub repository

## 📋 Step-by-Step Deployment

### Step 1: Create Redis Cloud Account (5 minutes)

1. [ ] Go to https://redis.com/try-free/
2. [ ] Sign up with email or GitHub
3. [ ] Click "Create database"
4. [ ] Configure:
   - Name: `convertx-redis`
   - Cloud: AWS
   - Region: Choose closest to you (e.g., us-east-1)
   - Type: Redis Stack
   - Plan: **Free (30MB)**
5. [ ] Click "Create database"
6. [ ] **SAVE THESE VALUES** (you'll need them later):
   ```
   Endpoint: redis-xxxxx.c1.us-east-1-1.ec2.cloud.redislabs.com
   Port: 12345
   Password: your-password-here
   ```

### Step 2: Deploy Backend to Render.com (10 minutes)

#### 2.1 Create Render Account
1. [ ] Go to https://render.com
2. [ ] Sign up with GitHub (recommended)
3. [ ] Authorize Render to access your repositories

#### 2.2 Deploy API Service
1. [ ] Click "New +" → "Web Service"
2. [ ] Select your GitHub repository
3. [ ] Configure:
   - **Name**: `convertx-api`
   - **Region**: Oregon (Free)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 "app.api:create_app()"
     ```
   - **Instance Type**: **Free**

4. [ ] Add Environment Variables (click "Advanced" → "Add Environment Variable"):
   ```
   FLASK_ENV = production
   PYTHON_VERSION = 3.11.0
   UPLOAD_FOLDER = /tmp/uploads
   OCR_ENGINE = surya
   REDIS_HOST = [your-redis-endpoint from Step 1]
   REDIS_PORT = [your-redis-port from Step 1]
   REDIS_PASSWORD = [your-redis-password from Step 1]
   REDIS_DB = 0
   ```

5. [ ] Click "Create Web Service"
6. [ ] Wait 5-10 minutes for deployment
7. [ ] **SAVE YOUR API URL**: `https://convertx-api.onrender.com`

#### 2.3 Deploy Celery Worker
1. [ ] Click "New +" → "Background Worker"
2. [ ] Select same GitHub repository
3. [ ] Configure:
   - **Name**: `convertx-celery`
   - **Region**: Oregon (Free)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     celery -A app.celery_app worker --loglevel=info --concurrency=1
     ```
   - **Instance Type**: **Free**

4. [ ] Add same Environment Variables as API service
5. [ ] Click "Create Background Worker"
6. [ ] Wait for deployment

### Step 3: Deploy Frontend to Vercel (5 minutes)

1. [ ] Go to https://vercel.com
2. [ ] Sign up with GitHub
3. [ ] Click "Add New..." → "Project"
4. [ ] Import your GitHub repository
5. [ ] Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
   - **Install Command**: `npm install` (auto-detected)

6. [ ] Add Environment Variable:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://convertx-api.onrender.com/api` (your Render API URL from Step 2.2)

7. [ ] Click "Deploy"
8. [ ] Wait 2-3 minutes
9. [ ] **SAVE YOUR FRONTEND URL**: `https://your-project.vercel.app`

### Step 4: Update CORS Settings (2 minutes)

1. [ ] Go to your Render dashboard
2. [ ] Click on `convertx-api` service
3. [ ] Click "Environment"
4. [ ] Add new environment variable:
   ```
   ALLOWED_ORIGINS = https://your-project.vercel.app
   ```
5. [ ] Click "Save Changes"
6. [ ] Service will auto-redeploy (takes 2-3 minutes)

### Step 5: Test Your Deployment (5 minutes)

1. [ ] Visit your Vercel URL: `https://your-project.vercel.app`
2. [ ] Upload a small PDF file (1-2 pages)
3. [ ] **IMPORTANT**: First request takes 30-60 seconds (services waking up)
4. [ ] Wait for conversion to complete
5. [ ] Download the Word document
6. [ ] Verify the conversion worked correctly

### Step 6: Keep Services Awake (Optional - 5 minutes)

To prevent the 30-60 second wake-up time:

1. [ ] Go to https://uptimerobot.com
2. [ ] Sign up (free)
3. [ ] Click "Add New Monitor"
4. [ ] Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: ConvertX API
   - **URL**: `https://convertx-api.onrender.com/api/health`
   - **Monitoring Interval**: 14 minutes
5. [ ] Click "Create Monitor"
6. [ ] Your service will now stay awake 24/7!

## 🎉 Deployment Complete!

Your ConvertX application is now live and accessible at:
- **Frontend**: https://your-project.vercel.app
- **Backend API**: https://convertx-api.onrender.com

## 📊 What You Get (Free Tier)

| Service | Free Tier Limits | Enough For |
|---------|------------------|------------|
| Vercel | Unlimited bandwidth | ✅ Unlimited users |
| Render API | 750 hours/month | ✅ 24/7 uptime |
| Render Worker | 750 hours/month | ✅ 24/7 uptime |
| Redis Cloud | 30MB storage | ✅ ~1000 jobs |

## ⚠️ Important Notes

### Free Tier Limitations
- Services sleep after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds
- Use UptimeRobot to keep services awake (optional)

### When Services Wake Up
- Show "Waking up server..." message to users
- This only happens on first request after 15 min idle
- Subsequent requests are instant

### Storage Limits
- Redis: 30MB (automatically evicts old data)
- Render: /tmp storage (cleared on restart)
- Files are cleaned up after 24 hours automatically

## 🔧 Troubleshooting

### Issue: "Connection refused" or "Cannot connect to Redis"
**Solution**: Check Redis credentials in Render environment variables

### Issue: "Service Unavailable" 
**Solution**: Wait 30-60 seconds for service to wake up

### Issue: Frontend can't reach backend
**Solution**: Check VITE_API_URL in Vercel environment variables

### Issue: CORS errors
**Solution**: Add your Vercel URL to ALLOWED_ORIGINS in Render

### Issue: Conversion fails
**Solution**: Check Celery worker logs in Render dashboard

## 📈 Monitoring Your App

### Render Dashboard
- View logs: Click service → "Logs" tab
- Check status: Green = running, Yellow = deploying
- Monitor usage: "Metrics" tab

### Vercel Dashboard
- View deployments: "Deployments" tab
- Check analytics: "Analytics" tab
- Monitor errors: "Logs" tab

### Redis Cloud Dashboard
- Check memory usage
- View connection count
- Monitor commands/sec

## 🚀 Next Steps

### Optional Improvements
- [ ] Add custom domain (free with Vercel)
- [ ] Set up email notifications
- [ ] Add Google Analytics
- [ ] Create API documentation
- [ ] Add rate limiting

### When to Upgrade
Consider paid plans when you need:
- No sleep time (instant responses)
- More than 100 conversions/day
- More than 30MB Redis storage
- Custom domain with SSL on all services
- Priority support

## 💰 Cost to Upgrade (Optional)

If you outgrow free tier:
- Render Starter: $7/month per service ($14 total)
- Redis Cloud: $5/month for 100MB
- Vercel Pro: $20/month (optional)
- **Total**: $19-39/month for production-grade hosting

## 🎓 Learning Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Redis Cloud Documentation](https://docs.redis.com/latest/rc/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)

---

**Congratulations!** 🎉 Your ConvertX application is now live and accessible to the world, completely free!

Share your URL: `https://your-project.vercel.app`
