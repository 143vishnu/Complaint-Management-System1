# Vercel Deployment Guide

## 🚀 Deploy Frontend to Vercel

### Prerequisites
- GitHub account connected to Vercel
- Backend already deployed (e.g., Render, Railway, Heroku)

### Step-by-Step Deployment

#### 1. Push Code to GitHub
```bash
cd "C:\Users\Admin\Desktop\Complaint Management System1"
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

#### 2. Import Project to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Select your repository: `143vishnu/Complaint-Management-System1`
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `FE-main`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

#### 3. Set Environment Variables
In Vercel project settings → Environment Variables, add:

| Name | Value | Environment |
|------|-------|-------------|
| `VITE_API_URL` | `https://your-backend-url.com` | Production |

**Important:** Replace `https://your-backend-url.com` with your actual backend URL (e.g., from Render, Railway, or Heroku)

#### 4. Deploy
Click **"Deploy"** and wait for build to complete.

### Common 404 Error Fixes

#### Issue: All routes return 404
**Solution:** Already fixed in `vercel.json` with:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

#### Issue: API calls fail
**Solutions:**
1. **Check Environment Variable:**
   - Go to Vercel → Project Settings → Environment Variables
   - Verify `VITE_API_URL` is set correctly
   - Redeploy after adding/changing variables

2. **Check Backend CORS:**
   - Your backend must allow the Vercel domain
   - In `BE-main/server.py`, update CORS settings:
   ```python
   CORS(app, resources={
       r"/api/*": {
           "origins": [
               "http://localhost:5173",
               "http://localhost:5174",
               "https://your-vercel-app.vercel.app"  # Add this
           ]
       }
   })
   ```

3. **Check Backend is Running:**
   - Visit your backend URL directly: `https://your-backend-url.com/api`
   - Should return JSON with API endpoints

#### Issue: Build fails
**Common causes:**
- Node version mismatch
  - Go to Vercel → Project Settings → General → Node.js Version
  - Set to `18.x` or `20.x`
  
- Missing dependencies
  - Ensure `package.json` has all dependencies
  - Delete `node_modules` and `package-lock.json`, then `npm install`

### Test Deployment

After deployment succeeds:

1. **Visit your Vercel URL**: `https://your-project.vercel.app`
2. **Test Login/Signup**
3. **Test Creating Complaint**
4. **Check Browser Console** (F12) for any API errors

### Redeploy After Changes

```bash
git add .
git commit -m "Update description"
git push origin main
```

Vercel will auto-deploy on every push to `main` branch.

## 🔧 Troubleshooting

### Check Logs
Vercel → Your Project → Deployments → Click deployment → View Function Logs

### Environment Variables Not Working
1. Environment variables must start with `VITE_` for Vite
2. After changing env vars, you MUST redeploy
3. Clear browser cache after deployment

### Still Getting 404?
1. Check Vercel deployment logs for build errors
2. Verify `FE-main` is set as root directory
3. Ensure `vercel.json` is in `FE-main` folder
4. Try manual redeploy: Vercel → Deployments → Three dots → Redeploy

## 📞 Need Help?

Common issues checklist:
- ✅ `VITE_API_URL` environment variable set in Vercel
- ✅ Backend URL is accessible (test in browser)
- ✅ CORS configured on backend
- ✅ `.env` file NOT committed to GitHub (optional, for security)
- ✅ `vercel.json` in `FE-main` folder
- ✅ Root directory set to `FE-main` in Vercel settings
