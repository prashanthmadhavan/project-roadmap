# Phase 0: Foundation — Project Setup & Core Architecture

**Phase Goal:** Establish the basic architecture, repository, project structure, and core data model for the Task Gantt Chart application.

**Status:** ✓ COMPLETED

---

## Overview

Phase 0 establishes the foundational infrastructure for the Task Gantt Chart project—a multi-user project management tool with persistent storage, task dependency tracking, and interactive Gantt chart visualization.

### Key Outcomes
- GitHub repository created and configured
- Core application structure (Python server + HTML/CSS/JavaScript frontend)
- PostgreSQL + SQLite hybrid database architecture
- User authentication system with password hashing
- Session management with 15-minute timeout
- Multi-project support with user scoping
- Task CRUD operations
- Dependency management
- Basic Gantt chart visualization

---

## Requirements Met

### R1: Multi-Project Management
- ✓ Users can create multiple projects
- ✓ Projects are user-scoped (users only see their own)
- ✓ Project CRUD operations implemented

### R2: Task Management
- ✓ Create, read, update, delete tasks
- ✓ Tasks have start/end dates (day precision)
- ✓ Task dependencies tracked and validated
- ✓ Automatic dependency creation during task add

### R3: Data Persistence
- ✓ PostgreSQL for production (Render.com)
- ✓ SQLite fallback for local development
- ✓ Database schema: users, projects, tasks, dependencies tables
- ✓ Migration-free hybrid approach

### R4: User Authentication
- ✓ Username/password authentication
- ✓ PBKDF2-HMAC-SHA256 password hashing (standard library)
- ✓ Token-based session management
- ✓ 15-minute inactivity timeout with warning
- ✓ Demo user (demo/Demo@1234) with sample data

### R5: Gantt Chart Visualization
- ✓ D3.js-based interactive Gantt chart
- ✓ Weekday-only display (Mon-Fri grid)
- ✓ Weekend visualization (light gray blocks)
- ✓ Orange dependency arrows (curved lines)
- ✓ Task bars show on-bar labels (smart truncation)
- ✓ Task names on left axis (full names with truncation for >25 chars)

### R6: Deployment Ready
- ✓ Render.com configuration (render.yaml)
- ✓ PostgreSQL service provisioning
- ✓ Auto-deploy on GitHub push
- ✓ GitHub repository connected

---

## Architecture

### Frontend
- **File:** `index.html` (1508 lines)
- **Tech:** Vanilla JavaScript, D3.js v7, HTML5, CSS3
- **Features:**
  - Login/authentication UI
  - Multi-project selector
  - Task creation form
  - Responsive Gantt chart
  - Task list view

### Backend
- **File:** `server.py` (1174 lines)
- **Tech:** Python 3 (http.server)
- **Features:**
  - RESTful API endpoints
  - Database abstraction layer
  - User authentication & authorization
  - Session token management
  - CORS support

### Database
- **Production:** PostgreSQL (Render service)
- **Development:** SQLite (task_gantt.db)
- **Schema:**
  - `users` — username, password_hash, created_at
  - `projects` — id, user_id, name, description
  - `tasks` — id, project_id, name, start_date, end_date, created_at
  - `dependencies` — task_id, depends_on_id

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| PostgreSQL + SQLite hybrid | Production DB without forcing local PostgreSQL dependency |
| PBKDF2 hashing (no external libs) | Secure, built-in to Python standard library |
| Token-based sessions | Stateless authentication, no server-side session storage |
| D3.js for Gantt | Powerful visualization, supports drag-and-drop, dependency arrows |
| Weekday-only grid | Business-focused view, visual weekend blocks for context |
| User scoping from day 1 | Security best practice, multi-user from foundation |
| Demo user auto-created | Clear onboarding, sample data for testing |

---

## Known Limitations (Phase 0)

1. **No drag-and-drop** — Initial implementation focuses on core CRUD
2. **No swimlane reordering** — Tasks displayed in creation order
3. **Limited task fields** — Only name, dates, dependencies (no priority, assignee, etc.)
4. **No task filtering/search** — All tasks shown in Gantt
5. **No permissions/roles** — All users have full access to their projects
6. **No bulk operations** — Create/edit one task at a time
7. **No undo/redo** — Changes are immediate and irreversible
8. **No notifications** — No dependency conflict warnings

---

## API Endpoints (Implemented)

### Authentication
- `POST /api/auth/login` — User login, returns token
- `POST /api/auth/logout` — Clear session
- `GET /api/auth/user` — Get current user info

### Projects
- `GET /api/projects` — List user's projects
- `POST /api/projects` — Create new project
- `PUT /api/projects/{id}` — Update project
- `DELETE /api/projects/{id}` — Delete project

### Tasks
- `GET /api/projects/{id}/tasks` — List tasks (included in projects endpoint)
- `POST /api/projects/{id}/tasks` — Create task
- `PUT /api/projects/{id}/tasks/{id}` — Update task
- `DELETE /api/projects/{id}/tasks/{id}` — Delete task

---

## Testing & Validation

### Manual Testing
- ✓ User registration flow (demo user)
- ✓ Authentication token generation
- ✓ Project CRUD operations
- ✓ Task CRUD operations
- ✓ Dependency creation and validation
- ✓ Gantt chart rendering
- ✓ Session timeout at 15 minutes

### Browser Testing
- ✓ Chrome/Safari (macOS)
- ✓ Responsive layout
- ✓ D3 chart rendering

### Database Testing
- ✓ PostgreSQL connection (Render)
- ✓ SQLite fallback (local)
- ✓ Data persistence across restarts

---

## Defects Fixed (Phase 0)

1. ✓ **Initial schema issues** — Tables created on first run
2. ✓ **Token persistence** — localStorage backup + server validation
3. ✓ **Demo user isolation** — Only created on first DB init
4. ✓ **User scoping** — Queries filtered by user_id throughout

---

## Deliverables

### Code
- ✓ `index.html` — Complete frontend application
- ✓ `server.py` — Python HTTP server with API
- ✓ `render.yaml` — Render.com deployment config

### Documentation
- ✓ `README.md` — Project overview and usage
- ✓ `AUTHENTICATION.md` — Auth system details
- ✓ `RENDER_SETUP.md` — PostgreSQL manual setup guide

### Repository
- ✓ GitHub repository: https://github.com/prashanthmadhavan/project-roadmap
- ✓ 15+ commits with clear messages
- ✓ Auto-deploy on push enabled

---

## Success Criteria

- [x] Core application runs locally
- [x] Database persists data
- [x] Users can authenticate
- [x] Projects and tasks are CRUD-able
- [x] Gantt chart renders with dependencies
- [x] Renders displays/auto-deploys
- [x] Multi-user support works
- [x] Session timeout enforced

---

## Phase 0 Retrospective

### What Went Well
- Solid architecture from day 1 (user scoping, DB abstraction)
- Hybrid DB approach eliminated local PostgreSQL dependency
- Token system enables stateless authentication
- D3 Gantt chart provides good foundation for interactivity

### Challenges Overcome
- Initial custom xScale function broke drag calculations → Restored D3 scaleTime()
- Task rendering defects after updates → Fixed by reloading projects from server
- Drag event listener duplication → Moved to global scope, added once

### Technical Debt
- No UI spec document (being created in Phase 1)
- Limited error handling in frontend
- No logging beyond console.error
- API responses lack pagination

---

## Next Phase: Phase 1 (UI/UX Polish)

Phase 1 will focus on:
- Creating formal UI-SPEC.md design contract
- Implementing drag-to-move functionality (already partially working)
- Swimlane reordering (vertical drag)
- Smart task name truncation
- Improved error messaging
- Responsive design refinements

**Estimated Duration:** 2-3 days

---

**Phase 0 Status:** ✓ COMPLETE

Last updated: 2026-05-08
