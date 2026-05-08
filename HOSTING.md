# Hosting Guide - Project Roadmap

Your code is now on GitHub! Here are the best ways to host it.

**Repository**: https://github.com/prashanthmadhavan/project-roadmap

---

## Quick Comparison

| Platform | Cost | Setup Time | Features | Best For |
|----------|------|------------|----------|----------|
| GitHub Pages | Free | 5 min | Static hosting | Read-only viewing |
| Render | Free | 10 min | Full Python backend | Production with data persistence |
| Railway | Free | 10 min | Full Python backend | Production alternative |
| PythonAnywhere | Free | 10 min | Beginner-friendly | Learning/testing |
| Replit | Free | 5 min | No-config hosting | Quick demos |

---

## Option 1: GitHub Pages (Static Only - Read Only)

**Best for**: Quick preview, no data persistence needed

### Setup (2 minutes)

1. Go to your repository: https://github.com/prashanthmadhavan/project-roadmap
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main** / **root**
   - Click **Save**
4. Wait 1-2 minutes for deployment
5. Your site will be live at: https://prashanthmadhavan.github.io/project-roadmap/

### Limitations
- ❌ Cannot add new tasks (API won't work)
- ❌ Data won't persist
- ✓ Can view existing tasks and Gantt chart
- ✓ Free and automatic

---

## Option 2: Render.com (Full Functionality - RECOMMENDED)

**Best for**: Full-featured production app with data persistence

### Setup (10 minutes)

1. Go to https://render.com
2. Click **New +** → **Web Service**
3. Select **GitHub** and authorize
4. Choose repository: **project-roadmap**
5. Fill in:
   - **Name**: project-roadmap
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 server.py`
6. Click **Create Web Service**
7. Wait for deployment (2-5 minutes)
8. Your app URL will appear at the top of the page

### Features
- ✓ Full functionality (add/edit/delete tasks)
- ✓ Data persistence (tasks saved on server)
- ✓ Free tier with limitations
- ✓ Auto-deploys on GitHub push
- ✓ Custom domain support

### Data Persistence
- Tasks are stored in `tasks.json` on the server
- Survive restarts (on free tier: ~15 min inactivity timeout)
- Backup by pulling from GitHub

---

## Option 3: Railway.app (Full Functionality)

**Best for**: Alternative to Render with slightly different pricing

### Setup (10 minutes)

1. Go to https://railway.app
2. Click **New Project** → **Deploy from GitHub**
3. Select your repository
4. Auto-detects Python/Flask automatically
5. Configure environment:
   - PORT: 8000 (auto-configured)
   - Add any custom vars
6. Click **Deploy**
7. Your deployment domain will be shown

### Features
- ✓ Full functionality
- ✓ Data persistence
- ✓ Free tier: $5/month credit (usually covers 1 app)
- ✓ Easy scaling

---

## Option 4: PythonAnywhere (Beginner Friendly)

**Best for**: Learning Python, simple apps

### Setup (15 minutes)

1. Go to https://www.pythonanywhere.com
2. Create free account
3. Click **Web** → **Add a new web app**
4. Choose **Manual configuration** → **Python 3.9**
5. In the web app config:
   - WSGI configuration file: Point to server.py
   - Upload your files via "Files" section
6. Click **Reload**

---

## Option 5: Replit (Fastest)

**Best for**: Quick demos, zero-config deployment

### Setup (5 minutes)

1. Go to https://replit.com
2. Click **Create** → **Import from GitHub**
3. Paste: https://github.com/prashanthmadhavan/project-roadmap
4. Select **Python** as language
5. Replit auto-configures everything
6. Click **Run**
7. Your public URL appears on the right

### Features
- ✓ Zero configuration
- ✓ Live collaboration
- ✓ Free tier works great
- ✓ Instant deployment

---

## My Recommendation

**For Production**: Use **Render.com**
- Free tier is generous
- Auto-deploys on push
- Data persists
- Best performance

**For Testing/Learning**: Use **Replit**
- Fastest setup
- Great UI
- No config needed

**For Portfolio**: Use **GitHub Pages**
- Free forever
- Shows your code
- Note: API won't work, tasks read-only

---

## Deploying Updates

Once deployed, updates are automatic:

```bash
# Make changes locally
git add .
git commit -m "Update description"
git push origin main

# On Render/Railway: Auto-deploys within 1-2 minutes
# On GitHub Pages: Redeployed automatically
```

---

## Environment Variables

If using Render, Railway, or PythonAnywhere, set these variables:

```
FLASK_ENV=production
PORT=8000  (or provided by platform)
HOST=0.0.0.0
```

---

## Troubleshooting

### "Application not working" on Render/Railway
- Check logs in the deployment dashboard
- Verify Python 3.9+ is selected
- Restart the service

### "Tasks not saving"
- Check server logs for errors
- Verify server is running
- For GitHub Pages: This is normal (static only)

### "Cannot access at custom URL"
- Wait 5 minutes for DNS propagation
- Clear browser cache
- Check that service is "active" in dashboard

---

## Next Steps

1. **Deploy now** to Render.com (recommended)
2. **Share your URL** with team
3. **Monitor** via dashboard
4. **Update** by pushing to GitHub
5. **Scale** if needed

---

## Support

- Render support: https://support.render.com
- Railway support: https://railway.app/help
- GitHub Pages: https://docs.github.com/pages
- This project: Check README.md

---

**Happy deploying!** 🚀
