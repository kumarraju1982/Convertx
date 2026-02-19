# Quick Fix: Connect Vercel Frontend to Backend

## The Problem
Your frontend is deployed on Vercel (https://convertx-dun.vercel.app/) but your backend is running locally on your computer. The Vercel-hosted frontend cannot reach your local backend.

## The Solution
Deploy your backend to Render.com (free tier available)

## Steps to Fix (5-10 minutes)

### 1. Push Your Code to GitHub
```bash
git add .
git commit -m "Add deployment configuration"
git push
```

### 2. Deploy to Render.com
1. Go to https://render.com
2. Sign up/login (can use GitHub account)
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will detect `render.yaml` automatically
6. Click "Apply" to create services
7. Wait 5-10 minutes for deployment

### 3. Get Your Backend URL
After deployment completes, you'll see:
- **pdf-converter-api** service with a URL like: `https://pdf-converter-api.onrender.com`

Copy this URL!

### 4. Update Vercel
1. Go to https://vercel.com/dashboard
2. Select your "convertx" project
3. Go to **Settings** → **Environment Variables**
4. Click "Add New"
5. Enter:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://pdf-converter-api.onrender.com/api` (paste your URL + `/api`)
   - **Environment**: Production
6. Click "Save"
7. Go to **Deployments** tab
8. Click "..." on latest deployment → "Redeploy"

### 5. Test!
Visit https://convertx-dun.vercel.app/ and upload a PDF file!

## What Gets Deployed
- ✅ Redis (for job queue)
- ✅ Flask API (handles uploads)
- ✅ Celery Worker (processes conversions)
- ✅ Tesseract OCR (for text extraction)

## Important Notes

### First Request is Slow
Render's free tier spins down services after 15 minutes of inactivity. The first request after spin-down takes 30-60 seconds to wake up.

### Free Tier Limits
- 750 hours/month per service (enough for testing)
- Services may be slow to start
- For production, upgrade to paid tier ($7/month per service)

## Troubleshooting

### "Cannot connect to backend"
- Check Render dashboard - all 3 services should show "Live"
- Check Render logs for errors
- Verify VITE_API_URL in Vercel is correct

### "Conversion stuck at processing"
- Check Celery worker logs on Render
- Worker might be starting up (first time takes longer)

### Still not working?
Check the full DEPLOYMENT.md guide for detailed troubleshooting.
