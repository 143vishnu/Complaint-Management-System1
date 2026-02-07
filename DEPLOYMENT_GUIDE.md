# Deployment Guide - Render & Vercel Configuration

## 🚨 DOCKERFILE ERROR FIX

**Error:** `failed to read dockerfile: open Dockerfile: no such file or directory`

**Reason:** Build system couldn't find Dockerfile at the root level

---

## 📦 Backend Deployment (Render)

### ✅ New Root-Level Dockerfile Created
- **File:** `/Dockerfile` (at project root)
- **Automatically** builds from `BE-main/` directory
- **No configuration needed** in Render

### Option 1: Auto-Deploy (Recommended)

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Add root Dockerfile for deployment"
   git push origin main
   ```

2. **Go to Render Dashboard**
   - New → Web Service
   - Connect your GitHub repo

3. **Configure:**
   - **Repository:** `143vishnu/Complaint-Management-System1`
   - **Branch:** `main`
   - **Root Directory:** (LEAVE BLANK or `/`)
   - **Build Command:** `pip install -r BE-main/requirements.txt`
   - **Start Command:** `cd BE-main && python server.py`

4. **Environment Variables:** (crucial!)
   ```
   NEON_URI=your_database_url
   JWT_TOKEN=your_jwt_secret
   CLOUD_NAME=your_cloudinary_name
   CLOUD_API_KEY=your_api_key
   CLOUD_API_SECRET=your_api_secret
   FLASK_ENV=production
   ```

5. **Deploy** → Wait for success

### Option 2: Docker Build (If Code-based Fails)

1. **Same settings as above** but:
   - **Runtime:** `Docker`
   - Build system will use `/Dockerfile` automatically

2. Set **Environment Variables** (same as above)

3. **Deploy**

---

## 🎨 Frontend Deployment (Vercel)

### ✅ Vercel Configuration (Already Fixed)

**File:** `FE-main/vercel.json` (with proper rewrites and build config)

### Steps:

1. **Go to Vercel Dashboard**
   - New Project
   - Import your GitHub repo

2. **Configure Project:**
   - **Framework:** Vite
   - **Root Directory:** `FE-main`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install --legacy-peer-deps`

3. **Add Environment Variables:**
   - **Name:** `VITE_API_URL`
   - **Value:** Your Render backend URL (e.g., `https://your-app.onrender.com`)
     
     ⚠️ **IMPORTANT:** Use your actual Render URL, NOT `localhost`

4. **Deploy** → Vercel will handle everything

### ✅ Why It Works Now:
- `vercel.json` has proper **rewrites** for React Router
- `VITE_API_URL` environment variable configures API calls
- Vite build optimizes everything

---

## 🐳 Local Docker Testing (Optional)

### Build & Run Locally:

```bash
# Build images
docker-compose build

# Start both services
docker-compose up

# Access:
# - Backend: http://localhost:6969
# - Frontend: http://localhost:80
```

### Troubleshoot Docker:

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all
docker-compose down
```

---

## ✅ Deployment Checklist

### Before Deploying Backend:
- [ ] All environment variables set in Render
- [ ] Database connection (NEON_URI) working
- [ ] Cloudinary credentials (CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET)
- [ ] JWT_TOKEN secret set

### Before Deploying Frontend:
- [ ] Backend URL set in `VITE_API_URL` environment variable
- [ ] Frontend root directory set to `FE-main` in Vercel
- [ ] No hardcoded API URLs (should use `VITE_API_URL`)

### After Deployment:
- [ ] Test login/signup
- [ ] Test complaint submission
- [ ] Check browser console (F12) for API errors
- [ ] Test all main features

---

## 🔧 Common Issues & Fixes

### Issue: "Cannot GET /" on Frontend
**Solution:** Vercel `/` rewrite needs `vercel.json` with rewrites (already fixed)

### Issue: API returns CORS error
**Solution:** Backend needs CORS configured for your Vercel domain
- In `BE-main/server.py` line 39-52, add your Vercel URL:
  ```python
  "https://your-vercel-app.vercel.app"
  ```

### Issue: 404 on API calls
**Solution:** Check that `VITE_API_URL` is set correctly in Vercel
- Must be full URL: `https://your-backend.onrender.com`
- Must include `https://` (not `http://`)

### Issue: Build fails on Render
**Solution:** 
- Use **Code-based** build (not Docker) if Python dependencies fail
- Check requirements.txt is in `BE-main/`
- All environment variables must be set

### Issue: Environment variables not working on Vercel
**Solution:**
- Environment variables must start with `VITE_` for Vite
- After changing env vars, **REDEPLOY** the project
- Clear browser cache

---

## 📋 File Structure Explanation

```
Complaint-Management-System1/
├── Dockerfile                    ← Backend root (builds from BE-main/)
├── Dockerfile.frontend           ← Frontend nginx image
├── docker-compose.yml            ← Local development
├── BE-main/
│   ├── Dockerfile               ← Old (not used, kept for reference)
│   ├── server.py                ← Flask app entry point
│   ├── requirements.txt          ← Python dependencies
│   ├── models/
│   ├── routes/
│   └── utils/
└── FE-main/
    ├── vercel.json              ← Vercel deployment config
    ├── .env.example             ← Env variables template
    ├── vite.config.js           ← Vite build config
    ├── package.json             ← Node dependencies
    └── src/
```

---

## 🚀 Final Deployment Flow

```
1. Code in GitHub
    ↓
2. Push code to main branch
    ↓
3. Render auto-builds backend (uses root Dockerfile)
    ↓
4. Vercel auto-builds frontend (uses FE-main/vercel.json)
    ↓
5. Frontend env var points to Render URL
    ↓
6. Your app is live! 🎉
```

---

## 💡 Pro Tips

- **Auto-deploy:** Every push to `main` triggers build
- **Preview URLs:** Render and Vercel provide preview URLs
- **Free tier:** Both Render (free dynamic server) and Vercel (free frontend) have generous free tiers
- **Cold starts:** First request on free Render might be slow (spins up container)

---

## 📞 Still Getting Errors?

1. Check **Render Build Logs:** Render Dashboard → Deployments → View Logs
2. Check **Vercel Build Logs:** Vercel Dashboard → Deployments → View Logs
3. Verify all environment variables are set
4. Try local Docker test: `docker-compose up`
5. Check frontend console (F12) for network errors

Good luck! 🚀
