# Deploy to Render.com - Step by Step Guide

Your application is ready to deploy! This guide will walk you through deploying to Render.com in less than 10 minutes.

## Prerequisites

- GitHub account (you already have this: prashanthmadhavan)
- Render.com account (free to create)
- Your repository: https://github.com/prashanthmadhavan/project-roadmap

---

## Step-by-Step Deployment

### Step 1: Sign Up / Log In to Render.com

1. Go to https://render.com
2. Click **Sign up** (or **Log in** if you have an account)
3. **Sign up with GitHub** (easiest option)
   - Click "Continue with GitHub"
   - Authorize Render to access your GitHub
4. Complete your profile

### Step 2: Create a New Web Service

1. In your Render dashboard, click **New +** button (top right)
2. Select **Web Service**
   
   ![image](https://render.com/docs/images/getting-started/web-services.png)

### Step 3: Connect Your GitHub Repository

1. You'll see "Connect a repository"
2. Your GitHub account should be connected
3. In the search box, type: `project-roadmap`
4. Select: **prashanthmadhavan/project-roadmap**
5. Click **Connect**

### Step 4: Configure the Service

Fill in the following fields:

| Field | Value |
|-------|-------|
| **Name** | `project-roadmap` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python3 server.py` |
| **Instance Type** | `Free` |

**Leave these as default:**
- Root Directory: (empty)
- Auto-deploy: (checked)

### Step 5: Set Environment Variables (Optional)

You don't need to set any environment variables. The server will automatically use:
- PORT: 10000 (Render default)
- HOST: 0.0.0.0 (listening on all interfaces)

**Skip this section** and click **Create Web Service**

### Step 6: Wait for Deployment

Render will now:
1. Build your application (1-2 minutes)
2. Start your server (30 seconds)
3. Make it live (instantly)

**You'll see:**
- "Build in progress" → spinning icon
- "Deploying" → another spinning icon
- "Live" → green checkmark with a URL

This usually takes **2-5 minutes total**.

### Step 7: Get Your URL

Once deployment is complete, you'll see your public URL:

```
https://project-roadmap-xxxxxx.onrender.com
```

This is your live application URL!

---

## After Deployment ✅

### Access Your Application

1. Click the URL in Render dashboard
2. Or visit: `https://project-roadmap-xxxxxx.onrender.com`
3. You should see your Gantt chart with all 52 tasks

### Test Full Functionality

1. **Add a task:**
   - Enter task name: "Test Task"
   - Select start/end dates
   - Click "Add Task"
   - Check if it appears in the chart

2. **Edit a task:**
   - Click "Edit" on any task
   - Modify the details
   - Click "Save"

3. **Delete a task:**
   - Click "Delete"
   - Confirm deletion

4. **Add dependencies:**
   - Select a task from the dropdown
   - Click "Add Dependency"
   - View the orange arrows in the chart

### Share Your Application

Your URL is public and shareable:
```
https://project-roadmap-xxxxxx.onrender.com
```

Share with your team to let them view and manage tasks!

---

## Common Issues & Solutions

### Issue: Build Failed
**Solution:**
- Check the build logs in Render dashboard
- Usually means a Python dependency is missing
- Contact Render support with the log output

### Issue: Application Shows 502 Error
**Solution:**
- Wait 30 seconds and refresh
- Check if server is running in Render logs
- Restart the service: Settings → Restart Service

### Issue: Tasks Not Saving
**Solution:**
- Check Render logs for errors
- Verify the API endpoint is `/api/tasks`
- Try adding a simple task first

### Issue: Free Tier Running Out
**Solution:**
- Render free tier includes limited hours per month
- After 750 free hours, you'll be charged
- Upgrade to paid ($7/month) for unlimited
- Or delete unused services

---

## Data Persistence

Your tasks are saved in `tasks.json` file on the Render server.

**Important Notes:**
- Free tier instances sleep after 15 minutes of inactivity
- When they wake up, `tasks.json` is preserved
- Paid tier instances never sleep
- To back up your data, pull from GitHub

### Backup Your Data

```bash
# Pull latest data from your deployed app
curl https://project-roadmap-xxxxxx.onrender.com/api/tasks > backup.json
```

---

## Auto-Deployment

Whenever you push changes to GitHub:

```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will automatically:
1. Detect the push
2. Rebuild your application
3. Deploy the new version
4. Your URL stays the same

---

## Next Steps

1. ✅ Deploy to Render.com (this guide)
2. ✅ Test add/edit/delete functionality
3. ✅ Share URL with your team
4. ⬜ Add more tasks and manage your roadmap
5. ⬜ Customize styling/colors (optional)
6. ⬜ Set up custom domain (paid feature)

---

## Monitoring & Logs

Check your application's health in Render:

1. Go to your service in Render dashboard
2. Click **Logs** tab
3. See real-time logs as users interact with the app
4. Check for errors and performance

---

## Costs

**Render.com Free Tier:**
- ✅ Free for first 750 hours/month (~31 days)
- ✅ Auto-sleep after 15 min inactivity
- ✅ No credit card needed
- ❌ Slower wake-up time

**Upgrade to Paid ($7/month):**
- ✅ Always on (no sleep)
- ✅ Better performance
- ✅ Priority support
- ✅ More reliable for production

---

## Support

- **Render Docs**: https://render.com/docs
- **Render Support**: https://support.render.com
- **GitHub Issues**: https://github.com/prashanthmadhavan/project-roadmap/issues

---

## Quick Reference

| Item | Value |
|------|-------|
| Service Type | Web Service |
| Language | Python 3 |
| Repository | prashanthmadhavan/project-roadmap |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python3 server.py` |
| Port | 10000 (auto) |
| Cost | Free tier or $7/month paid |

---

**Ready? Start at Step 1 above!** 🚀

After deployment, you can share your URL and start managing tasks with your team.
