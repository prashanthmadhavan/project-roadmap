# Task Gantt Chart Application

**Status**: Production (deployed to Render)
**Repository**: https://github.com/prashanthmadhavan/project-roadmap
**Live App**: https://project-roadmap.onrender.com

---

## Core Value

Multi-user task management and Gantt chart visualization with drag-and-drop scheduling and advanced feature toggles.

---

## Tech Stack

- **Backend**: Python 3 (SimpleHTTPServer)
- **Database**: PostgreSQL (Render production) / SQLite (local dev)
- **Frontend**: HTML5, CSS3, D3.js
- **Deployment**: Render (auto-deploy on GitHub push)
- **Authentication**: Token-based sessions (15-min timeout)

---

## Key Features

### Basic Mode (Always Available)
- User registration and login
- Project CRUD
- Task CRUD
- Task dependencies
- Static Gantt view
- Session-based auth

### Advanced Mode (Feature Toggle)
- Drag & drop task bars (reschedule)
- Swimlane reordering
- 3-week sliding timeline window
- Advanced Gantt controls

---

## Evolution Rules

1. **Data Isolation**: Users only see their own projects and tasks
2. **Session Timeout**: 15 minutes of inactivity → logout
3. **Feature Toggles**: Per-user advanced_mode setting (stored in database)
4. **Production First**: All changes tested before deployment
5. **No Breaking Changes**: API must remain backward-compatible

---

## Requirements

- ✓ Multi-user authentication
- ✓ Persistent data (PostgreSQL/SQLite)
- ✓ Gantt chart visualization
- ✓ Drag & drop (advanced mode)
- ✓ Feature toggles
- ✓ Session management
- ✓ Data isolation
- ✓ Auto-deployment via Render

