# Deployment Guide

## Current Status
- **Frontend**: Deployed on Vercel at https://convertx-dun.vercel.app/
- **Backend**: Running locally (needs to be deployed)

## Problem
The Vercel-hosted frontend cannot connect to your local backend. You need to deploy the backend to a cloud service.

## Solution: Deploy Backend to Render.com (Free)

### Step 1: Prepare Your Repository

1. Make sure all your code is committed to Git:
```bash
git add .
git commit -m "Prepare for deployment"
git push
```

### Step 2: Deploy to Render.com

1. Go to https://render.com and sign up/login
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to create all services (Redis, API, Worker)

### Step 3: Get Your Backend URL

After deployment, Render will give you a URL like:
```
https://pdf-converter-api.onrender.com
```

### Step 4: Update Vercel Environment Variable

1. Go to your Vercel dashboard
2. Select your project (convertx)
3. Go to Settings → Environment Variables
4. Add a new variable:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://pdf-converter-api.onrender.com/api` (use your actual Render URL)
5. Redeploy your frontend

### Step 5: Test

Visit https://convertx-dun.vercel.app/ and try uploading a PDF!

## Alternative: Quick Test with ngrok (Temporary)

If you want to test quickly without deploying:

1. Install ngrok: https://ngrok.com/download
2. Start your Flask backend locally: `flask run`
3. In another terminal, run: `ngrok http 5000`
4. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
5. Update Vercel environment variable `VITE_API_URL` to `https://abc123.ngrok.io/api`
6. Redeploy frontend

**Note**: ngrok URLs expire when you close the tunnel, so this is only for testing.

## Important Notes

### Render.com Free Tier Limitations
- Services spin down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- 750 hours/month free (enough for one service running 24/7)

### Required for Production
- All three services must be running:
  1. **Redis** - For job queue and status
  2. **Flask API** - For handling requests
  3. **Celery Worker** - For processing conversions

### Tesseract on Render
Render's free tier doesn't include Tesseract by default. You'll need to add a build script:

Create `backend/render-build.sh`:
```bash
#!/bin/bash
apt-get update
apt-get install -y tesseract-ocr
pip install -r requirements.txt
```

Then update `render.yaml` buildCommand to:
```yaml
buildCommand: cd backend && chmod +x render-build.sh && ./render-build.sh
```

## Troubleshooting

### Backend not responding
- Check Render logs for errors
- Verify Redis is running
- Ensure Celery worker is active

### CORS errors
- Backend already has CORS configured for all origins
- If issues persist, check browser console for specific error

### Conversion fails
- Check Celery worker logs on Render
- Verify Tesseract is installed (check build logs)
- Ensure file upload size limits are configured

## Cost Optimization

For production, consider:
- **Render**: $7/month for persistent services
- **Railway**: Similar pricing with better free tier
- **AWS/GCP**: More complex but scalable
