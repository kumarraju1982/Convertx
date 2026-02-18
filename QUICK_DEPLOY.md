# ⚡ Quick Deploy Reference Card

## 🎯 30-Minute Free Deployment

### Step 1: Redis Cloud (5 min)
```
1. Go to: https://redis.com/try-free/
2. Sign up → Create database
3. Name: convertx-redis
4. Plan: Free (30MB)
5. Save: Host, Port, Password
```

### Step 2: Render Backend (10 min)
```
1. Go to: https://render.com
2. New+ → Web Service
3. Connect GitHub repo
4. Root Directory: backend
5. Build: pip install -r requirements.txt
6. Start: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 "app.api:create_app()"
7. Add env vars (see below)
8. Save API URL
```

**Environment Variables for Render:**
```
FLASK_ENV=production
PYTHON_VERSION=3.11.0
UPLOAD_FOLDER=/tmp/uploads
OCR_ENGINE=surya
REDIS_HOST=[your-redis-host]
REDIS_PORT=[your-redis-port]
REDIS_PASSWORD=[your-redis-password]
REDIS_DB=0
```

### Step 3: Render Celery (5 min)
```
1. New+ → Background Worker
2. Same repo, same root directory
3. Build: pip install -r requirements.txt
4. Start: celery -A app.celery_app worker --loglevel=info --concurrency=1
5. Add same env vars as Step 2
```

### Step 4: Vercel Frontend (5 min)
```
1. Go to: https://vercel.com
2. New Project → Import repo
3. Root Directory: frontend
4. Framework: Vite (auto-detected)
5. Add env var:
   VITE_API_URL=https://your-backend.onrender.com/api
6. Deploy
```

### Step 5: Update CORS (2 min)
```
1. Render → convertx-api → Environment
2. Add: ALLOWED_ORIGINS=https://your-project.vercel.app
3. Save (auto-redeploys)
```

### Step 6: Test (3 min)
```
1. Visit: https://your-project.vercel.app
2. Upload small PDF
3. Wait 30-60 sec (first time only)
4. Download Word doc
5. Done! 🎉
```

## 📋 Quick Checklist

- [ ] Redis Cloud account + credentials
- [ ] Render API deployed
- [ ] Render Celery deployed
- [ ] Vercel frontend deployed
- [ ] CORS updated
- [ ] Tested with PDF

## 🔗 Quick Links

- Redis Cloud: https://redis.com/try-free/
- Render: https://render.com
- Vercel: https://vercel.com
- UptimeRobot: https://uptimerobot.com (optional)

## 💡 Pro Tip

Set up UptimeRobot to ping `https://your-backend.onrender.com/api/health` every 14 minutes to keep services awake!

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check Redis credentials |
| Service unavailable | Wait 30-60 seconds |
| CORS error | Add Vercel URL to ALLOWED_ORIGINS |
| Conversion fails | Check Celery logs in Render |

## 📖 Full Guide

For detailed instructions, see: **FREE_DEPLOYMENT_CHECKLIST.md**

---

**Total Time**: 30 minutes
**Total Cost**: $0/month
**Result**: Live production app! 🚀
