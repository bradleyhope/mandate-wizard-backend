# 🚂 Railway Deployment Guide - Mandate Wizard

## Overview

This guide walks you through deploying the Mandate Wizard application (backend + frontend) on Railway.

## Prerequisites

- Railway account (https://railway.app)
- GitHub account with both repositories:
  - `mandate-wizard-backend`
  - `mandate-wizard-frontend`
- All required API keys and credentials ready

---

## 🎯 Step 1: Deploy Backend

### 1.1 Create New Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose `mandate-wizard-backend` repository

### 1.2 Configure Environment Variables

In the Railway dashboard, go to **Variables** and add the following:

#### **Required Database Variables**
```bash
PINECONE_API_KEY=pcsk_your_actual_key_here
PINECONE_INDEX_NAME=netflix-mandate-wizard
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
```

#### **Required OpenAI API**
```bash
OPENAI_API_KEY=sk-your_openai_key_here
```

#### **Required Ghost CMS Authentication**
```bash
GHOST_URL=https://hollywood-signal.ghost.io
GHOST_ADMIN_ID=your_ghost_admin_id
GHOST_ADMIN_SECRET=your_ghost_admin_secret
GHOST_CONTENT_KEY=your_ghost_content_key
```

#### **Flask Configuration**
```bash
FLASK_ENV=production
SECRET_KEY=generate_a_random_32_character_string_here
```

#### **CORS Configuration** (⚠️ Add after frontend is deployed)
```bash
# Leave this empty initially - you'll add it after deploying frontend
FRONTEND_URL=
```

### 1.3 Deploy

1. Railway will automatically detect the `Procfile` and deploy
2. Wait for deployment to complete (5-10 minutes first time)
3. **Copy the backend URL** from Railway dashboard (e.g., `https://mandate-wizard-backend-production.up.railway.app`)

---

## 🎨 Step 2: Deploy Frontend

### 2.1 Create New Project

1. In Railway, click **"New Project"** again
2. Select **"Deploy from GitHub repo"**
3. Choose `mandate-wizard-frontend` repository

### 2.2 Configure Environment Variables

In the Railway dashboard, go to **Variables** and add:

```bash
# Backend API URL (use the URL from Step 1.3)
VITE_API_URL=https://mandate-wizard-backend-production.up.railway.app

# Application Settings
VITE_APP_TITLE=Mandate Wizard
```

### 2.3 Deploy

1. Railway will build and deploy the frontend
2. Wait for deployment to complete
3. **Copy the frontend URL** from Railway dashboard (e.g., `https://mandate-wizard-frontend-production.up.railway.app`)

---

## 🔗 Step 3: Connect Frontend and Backend

### 3.1 Update Backend CORS

1. Go back to **backend project** in Railway
2. Add/update the following variables:

```bash
FRONTEND_URL=https://your-frontend-url.up.railway.app
```

3. Click **"Redeploy"** on the backend

### 3.2 Verify Connection

1. Visit your frontend URL
2. Open browser DevTools → Console
3. Try asking a question in the Query interface
4. Check that there are no CORS errors

---

## 🎭 Step 4: Configure Custom Domain (Optional)

### For Frontend:
1. Go to frontend project → **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `mandatewizard.com`)
4. Update your DNS records as instructed by Railway

### For Backend:
1. Go to backend project → **Settings** → **Domains**
2. Add a subdomain (e.g., `api.mandatewizard.com`)
3. Update DNS records

### Update Environment Variables:
```bash
# Backend:
PRODUCTION_DOMAIN=mandatewizard.com

# Frontend:
VITE_API_URL=https://api.mandatewizard.com
```

---

## ✅ Step 5: Verify Deployment

### Test Checklist:

- [ ] Backend health check: Visit `https://your-backend-url.up.railway.app/`
- [ ] Frontend loads: Visit `https://your-frontend-url.up.railway.app/`
- [ ] Home page shows recent mandates
- [ ] Query page accepts questions
- [ ] Authentication works (try logging in)
- [ ] No CORS errors in browser console
- [ ] API responses are fast (check Network tab)

---

## 🐛 Troubleshooting

### Backend won't start
**Check logs in Railway dashboard:**
- Missing environment variables? → Add them
- Import errors? → Check `requirements.txt`
- Database connection failed? → Verify credentials

### Frontend can't connect to backend
**Check:**
1. `VITE_API_URL` is set correctly in frontend
2. `FRONTEND_URL` is set correctly in backend
3. No CORS errors in browser console
4. Backend is actually running (visit backend URL)

### 502 Bad Gateway
**This usually means:**
- Backend crashed during startup
- Check Railway logs for Python errors
- Verify all required env vars are set

### Authentication not working
**Check:**
1. Ghost CMS credentials are correct
2. Email `bradley@projectbrazen.com` has dev bypass (see `ghost_auth.py:159`)
3. `X-User-Email` header is being sent from frontend

---

## 📊 Monitoring

### Railway Dashboard
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: History and rollback options

### Application Logs
Backend logs show:
- Query cache hits/misses
- Response times
- Authentication attempts
- Error messages

---

## 💰 Cost Estimates

**Railway Pricing (as of 2025):**
- **Starter Plan**: $5/month
  - $5 of usage included
  - Additional usage: pay-as-you-go

**Expected Monthly Costs:**
- Backend (Python app): ~$15-25/month
- Frontend (Node.js): ~$5-10/month
- **Total**: $20-35/month for moderate usage

---

## 🔒 Security Checklist

Before going live:

- [ ] All hardcoded credentials removed from code
- [ ] Environment variables set in Railway (not in `.env` files)
- [ ] CORS configured with specific origins (no wildcards)
- [ ] Ghost CMS authentication properly configured
- [ ] Rate limiting enabled (check `rate_limiter.py`)
- [ ] HTTPS enabled on both frontend and backend
- [ ] Secret keys are random and secure

---

## 🚀 Going to Production

### Before Launch:
1. Remove dev bypass in `ghost_auth.py` (line 159)
2. Set rate limits appropriately for production
3. Enable monitoring/alerting in Railway
4. Test with real users
5. Have rollback plan ready

### Launch Day:
1. Monitor Railway logs closely
2. Watch for errors in browser console
3. Monitor response times
4. Be ready to rollback if issues occur

---

## 📞 Support

**Railway Issues:**
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app

**Application Issues:**
- Check application logs in Railway dashboard
- Review error messages in browser DevTools
- Test API endpoints directly with curl/Postman

---

## 🎉 Success!

Your Mandate Wizard should now be live and accessible!

**URLs:**
- Frontend: `https://your-frontend-url.up.railway.app`
- Backend API: `https://your-backend-url.up.railway.app`

Share the frontend URL with your beta users and start collecting feedback!
