# ✅ Code Pushed! Now Deploy to Render

Your code is now on GitHub: https://github.com/kumarraju1982/Convertx

## Step 1: Go to Render.com

Open this link: https://dashboard.render.com/

## Step 2: Sign Up / Login

- Click "Get Started" or "Login"
- **Recommended**: Use "Sign in with GitHub" for easier integration
- This will connect your GitHub account

## Step 3: Create New Blueprint

1. Click the **"New +"** button (top right)
2. Select **"Blueprint"** from the dropdown
3. You'll see "Connect a repository"

## Step 4: Connect Your Repository

1. Click **"Connect account"** if GitHub isn't connected yet
2. Find and select: **kumarraju1982/Convertx**
3. Click **"Connect"**

## Step 5: Review and Deploy

Render will automatically detect your `render.yaml` file and show:

- ✅ **pdf-converter-redis** (Redis database)
- ✅ **pdf-converter-api** (Flask web service)
- ✅ **pdf-converter-worker** (Celery worker)

Click **"Apply"** to start deployment!

## Step 6: Wait for Deployment (5-10 minutes)

You'll see three services building:
- Redis will be ready first (~1 minute)
- API and Worker will take 5-10 minutes (installing Tesseract)

Watch for all three to show **"Live"** status (green dot)

## Step 7: Get Your API URL

1. Click on **"pdf-converter-api"** service
2. At the top, you'll see a URL like:
   ```
   https://pdf-converter-api.onrender.com
   ```
3. **Copy this URL!**

## Step 8: Update Vercel

1. Go to: https://vercel.com/dashboard
2. Click on your **"convertx"** project
3. Go to **Settings** tab
4. Click **"Environment Variables"** in left sidebar
5. Click **"Add New"**
6. Fill in:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://pdf-converter-api.onrender.com/api` (paste your URL + `/api`)
   - **Environments**: Check "Production"
7. Click **"Save"**

## Step 9: Redeploy Frontend

1. Go to **"Deployments"** tab
2. Find the latest deployment
3. Click the **"..."** menu (three dots)
4. Click **"Redeploy"**
5. Confirm by clicking **"Redeploy"** again

Wait 1-2 minutes for redeployment to complete.

## Step 10: Test Your App! 🎉

1. Go to: https://convertx-dun.vercel.app/
2. Upload a PDF file
3. Watch it convert!

**Note**: First request might take 30-60 seconds as services wake up.

## Troubleshooting

### Services show "Deploy failed"
- Click on the service to see logs
- Common issue: Build timeout (try redeploying)

### "Cannot connect to backend"
- Make sure all 3 services show "Live" (green)
- Check you added `/api` at the end of the URL in Vercel
- Verify VITE_API_URL is set correctly

### Conversion stuck at "Processing"
- Check Celery worker logs on Render
- Worker might still be starting up (first time is slow)

### Still having issues?
Share the error message and I'll help debug!

---

## What You're Deploying

**Free Tier Includes:**
- Redis database (for job queue)
- Flask API (handles file uploads)
- Celery Worker (processes conversions)
- Tesseract OCR (text extraction)

**Limitations:**
- Services sleep after 15 min inactivity
- First request after sleep: 30-60 sec
- 750 hours/month per service (enough for testing)

**For Production:**
Upgrade to paid tier ($7/month per service) for:
- No sleep/spin-down
- Faster performance
- More resources
