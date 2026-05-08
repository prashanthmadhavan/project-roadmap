# Deployment Guide

## Push to GitHub

### Step 1: Create Repository on GitHub
Visit https://github.com/new and create a new repository:
- **Repository name**: `project-roadmap`
- **Description**: Interactive task management with Gantt chart visualization
- **Visibility**: Public (recommended for GitHub Pages)
- **Do NOT initialize with**: README, .gitignore, or license

### Step 2: Push Code
Once the repository is created, run:

```bash
cd /var/folders/0j/727fsw6n7b72vdhgshwp50tr0000gn/T/opencode/task-gantt
git push -u origin main
```

The code is now ready to push! All commits are prepared.

---

## Host on GitHub Pages

### Option A: Automatic Deployment (Recommended)

We need to set up a deployment script that serves the Python backend and static files on GitHub Pages.

**Note**: GitHub Pages serves static content only. For full functionality with the backend API:

1. **For Static Hosting Only** (Read-only task viewing):
   - Push the code (Step 2 above)
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` → `/root`
   - Your app will be at: `https://prashanthmadhavan.github.io/project-roadmap/`

2. **For Full Functionality** (With API and data persistence):
   You'll need a server that supports Python:
   - Heroku (free tier deprecated)
   - Render.com
   - Railway.app
   - PythonAnywhere
   - AWS Lambda + S3
   - Replit

### Option B: Deploy to Render.com (Free)

1. Sign up at https://render.com
2. Create new "Web Service"
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python server.py`
6. Environment: Set PORT=10000
7. Deploy!

### Option C: Deploy to Railway.app (Free)

1. Sign up at https://railway.app
2. Create new project
3. Connect GitHub repository
4. Set root directory: `/`
5. Railway auto-detects Python
6. Deploy!

---

## What Gets Deployed

### Static Files (Always needed)
- `index.html` - Main UI
- `generate_test_data.py` - Test data generator
- `roadmap_test_data.xlsx` - Reference data

### Backend Files (Needed for full functionality)
- `server.py` - Python HTTP server
- `tasks.json` - Task data storage

### Configuration
- `README.md` - Documentation
- `.gitignore` - Git rules
- `package.json` - Reference (Node modules not used)

---

## Environment Variables (if deploying to server)

If deploying to a service like Render or Railway, set:

```
PORT=10000  # or appropriate port for your service
HOST=0.0.0.0  # to accept connections from anywhere
```

---

## Running Locally vs. Production

### Local Development
```bash
python3 server.py
# Visit http://127.0.0.1:5000
```

### Production (Render/Railway)
Server automatically starts with appropriate PORT and HOST settings.

---

## Next Steps

1. **Immediate**: Create GitHub repo and push code
2. **Short-term**: Deploy to Render.com or Railway.app for full functionality
3. **Optional**: Set up GitHub Pages for static hosting as backup

Need help? Check the README.md for API documentation.
