# Render Deployment Guide - User Persistence

## Problem
User credentials may not persist across Render deployments if PostgreSQL is not properly configured.

## Solution
Ensure PostgreSQL is properly provisioned on Render:

### Step 1: Check PostgreSQL Database
1. Go to your Render dashboard
2. Look for "task-gantt-db" PostgreSQL database service
3. If it doesn't exist, create a new PostgreSQL database:
   - Service name: `task-gantt-db`
   - Plan: Free tier or higher
   - PostgreSQL Version: 15 (latest)

### Step 2: Verify Environment Variable
1. Go to your `project-roadmap` web service settings
2. Check "Environment" section
3. Should have environment variable: `DATABASE_URL`
4. Value should be auto-populated from the PostgreSQL service
5. If not, manually add it with the PostgreSQL connection string

### Step 3: Redeploy
1. Click "Rerun deploy" on the web service
2. Wait for deployment to complete (5-10 minutes)
3. Check logs for: "✓ PostgreSQL mode enabled"

## What to Look For in Logs
✓ Good: `✓ PostgreSQL mode enabled (DATABASE_URL set)`
✗ Bad: `⚠ DATABASE_URL not set - using SQLite`

## User Persistence
- **With PostgreSQL**: Users persist forever ✓
- **With SQLite**: Users are lost on restart ✗

## Testing Persistence
1. Register a new user
2. Wait 5+ minutes (or redeploy the service)
3. Try to login with the same credentials
4. Should succeed if using PostgreSQL

## Troubleshooting
If users still don't persist:
1. Check Render logs for database connection errors
2. Verify DATABASE_URL is set correctly
3. Ensure PostgreSQL service is "Running" (not "Building" or "Failed")
4. Try restarting the web service manually
5. Check PostgreSQL service logs for errors

## Local Development
- Runs on SQLite by default
- Data persists in `task_gantt.db` file
- To test PostgreSQL locally, set `DATABASE_URL` environment variable:
  ```bash
  export DATABASE_URL="postgresql://user:password@localhost/task_gantt"
  python3 server.py
  ```
