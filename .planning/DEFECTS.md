# Phase 1+ Defects & Feature Requests

**Date Reported:** 2026-05-08
**Status:** IN PROGRESS (Critical defects being fixed)

---

## Critical Defects (Must Fix)

### DEFECT-1: Missing Edit Task Functionality
**Severity:** CRITICAL
**Status:** OPEN

**Description:**
Users cannot edit existing tasks. Edit button (`.edit-btn`) is styled but has no onclick handler or event listener.

**Current Behavior:**
- Edit button visible in task list
- Click does nothing
- No modal or form appears

**Expected Behavior:**
- Click edit button → Modal/form appears with current task data
- User can modify task name, start date, end date, dependencies
- Save changes → Task updates in list and Gantt chart
- Cancel option available

**Impact:**
- Users must delete and recreate tasks to make changes
- Poor user experience
- High priority for production

**Affected Files:**
- `index.html` — Missing editTask() function and event handler

**Proposed Fix:**
1. Create editTask(taskId) function
2. Create edit modal/form component
3. Populate form with current task data
4. Handle save and cancel actions
5. Verify task updates in both list and Gantt

---

### DEFECT-2: Task Not Reflecting After Addition
**Severity:** CRITICAL
**Status:** OPEN

**Description:**
When user adds a new task, it appears in the list briefly but then disappears. Task does not persist in the UI immediately after creation.

**Current Behavior:**
- User fills form and clicks "Add Task"
- Task briefly appears in task list
- Task disappears (either from list or Gantt)
- Refresh page → Task appears correctly

**Expected Behavior:**
- Task appears and stays in both task list and Gantt chart immediately
- No refresh needed
- List and chart stay in sync

**Impact:**
- Users think tasks aren't being saved
- Requires page refresh to confirm
- Suggests data inconsistency

**Root Cause (Hypothesis):**
- `addTask()` calls `loadProjects()` which reloads from server
- But server response may not include newly created task immediately
- Or task list is being cleared before new data loaded
- Or Gantt chart is not re-rendering with new task

**Affected Files:**
- `index.html` — addTask() function, loadProjects(), renderGantt()
- `server.py` — POST /api/projects/{id}/tasks endpoint

**Proposed Fix:**
1. Debug the server response after task creation
2. Verify new task is returned in projects list
3. Check if renderGantt() is being called
4. Ensure Gantt chart re-renders with new task
5. Add optimistic UI update (show task immediately before server confirms)

---

### DEFECT-3: Drag and Drop Not Working
**Severity:** CRITICAL
**Status:** OPEN

**Description:**
Tasks cannot be dragged on the Gantt chart. Horizontal drag (to move dates) and vertical drag (to reorder) do not work.

**Current Behavior:**
- Mouse over task bar → Cursor shows "grab" icon
- Click and drag → Nothing happens
- Task doesn't move
- Dates don't change

**Expected Behavior:**
- Horizontal drag → Shifts task dates forward/backward
- Vertical drag → Reorders task in swimlane
- Visual feedback during drag (opacity, outline)
- Update persists after release

**Impact:**
- Core Gantt feature is broken
- Users cannot manipulate timeline
- Major UX regression

**Root Cause (Hypothesis):**
- Global event listeners (mousemove, mouseup) may not be firing
- Scale variables (currentXScale, currentYScale) may be undefined
- Event delegation change may have broken mouse event flow
- D3 event binding may be interfering with global listeners

**Affected Files:**
- `index.html` — Global mousemove/mouseup listeners, renderGantt(), drag math

**Proposed Fix:**
1. Verify global event listeners are attached (not removed)
2. Check currentXScale, currentYScale are initialized
3. Verify draggedBar is set by mousedown handler
4. Test drag math with console logging
5. Ensure D3 elements don't prevent event bubbling
6. Re-test with simple drag scenario

---

### DEFECT-4: Random Demo Data Persisted on User Switch
**Severity:** CRITICAL
**Status:** OPEN

**Description:**
When user logs out of demo account and logs into a new user, the new user sometimes has demo data (tasks from demo account) visible.

**Current Behavior:**
1. Login as demo → See demo tasks
2. Logout → Redirected to login
3. Create new user (e.g., "testuser") → Login
4. Sometimes see demo tasks in new user account
5. Refresh page → Demo data disappears (replaced with empty projects)

**Expected Behavior:**
- New user should only see their own projects/tasks
- No data from other users should be visible
- Projects should be properly scoped by user

**Impact:**
- Data privacy/isolation issue
- Users see each other's data
- Security vulnerability

**Root Cause (Hypothesis):**
- Projects array not cleared on logout
- User context not properly reset when switching users
- Demo data cache not being cleared
- Server returning data for wrong user

**Affected Files:**
- `index.html` — logout(), login(), projects array initialization
- `server.py` — GET /api/projects endpoint (user scoping)

**Proposed Fix:**
1. Clear projects array on logout
2. Clear authToken on logout
3. Verify server filters projects by current user
4. Check user scoping in database queries
5. Test logout/login cycle with different users

---

### DEFECT-5: User Not Persisting (Re-registration Required)
**Severity:** CRITICAL
**Status:** OPEN

**Description:**
When user logs out and logs back in with the same username, the account doesn't exist. User must re-register with same username.

**Current Behavior:**
1. Create new user "testuser" with password "Test@1234"
2. Create projects and tasks
3. Logout → Redirected to login
4. Login with "testuser" / "Test@1234" → "Invalid credentials" error
5. User must register again

**Expected Behavior:**
- User account persists in database
- Login with same credentials → Success
- Previously created data is available
- No re-registration needed

**Impact:**
- Users lose their data
- No account persistence
- Application is unusable for returning users

**Root Cause (Hypothesis):**
- Users not being saved to database during registration
- SQLite database not persisting users (only in-memory?)
- Server using different database for registration vs. login
- Demo user isolation breaking user creation

**Affected Files:**
- `server.py` — POST /api/auth/register, GET /api/auth/login, database initialization
- `index.html` — Registration form handling

**Proposed Fix:**
1. Verify users are saved to database during registration
2. Check database persistence (SQLite file exists and has data)
3. Verify login queries the database correctly
4. Test registration → logout → login cycle
5. Check server logs for database errors

---

## Feature Requests

### FEATURE-1: 3-Week Sliding Window with Timeline Slider
**Severity:** HIGH (Feature Request)
**Status:** PENDING

**Description:**
Replace full timeline view with a fixed 3-week window that shows exactly 21 days (3 weeks × 7 days). Add a horizontal slider at the bottom that shows the entire project timeline with a movable window indicator.

**Current Behavior:**
- Gantt shows all tasks from min to max date
- May show very long timelines (months or years)
- Difficult to see details for long projects
- No way to navigate through timeline

**Desired Behavior:**
1. **Fixed 3-Week View:**
   - Always show exactly 21 days (3 weeks)
   - Monday to Sunday for each 3-week period
   - Clear date headers showing week ranges

2. **Timeline Slider at Bottom:**
   - Horizontal slider showing full project timeline
   - Visual indicator of current 3-week window
   - Drag slider to move through timeline
   - Click on slider to jump to specific period

3. **Navigation:**
   - Previous / Next buttons (optional)
   - Jump to Today button
   - Date picker to select specific date

4. **Responsive:**
   - Slider adapts to project duration
   - Works on mobile (touch-friendly)

**User Experience:**
- Clearer view of near-term tasks
- Easier task management (not overwhelming)
- Better performance (fewer DOM elements)
- More intuitive navigation

**Implementation Approach:**
1. Keep current Gantt chart structure
2. Add xScale domain calculation based on current window
3. Add slider component below Gantt
4. Bind slider position to xScale domain
5. Update on slider drag
6. Persist slider position to localStorage

**Impact:**
- Improves usability for long-duration projects
- Reduces cognitive load
- Enables better task planning
- High-priority feature for production

---

## Defect Priority & Timeline

### Critical (Block Release)
1. **Edit Task** — Users need to modify tasks
2. **Task Persistence** — Tasks must appear immediately
3. **Drag & Drop** — Core Gantt feature
4. **User Persistence** — Users must not re-register
5. **Demo Data Isolation** — Privacy/security issue

### High (Next Release)
6. **3-Week Sliding Window** — UX improvement for long timelines

---

## Testing Plan

### Unit Tests Needed
- Edit task function with various inputs
- User registration/login persistence
- Project/task data isolation by user
- Drag calculations with various timeline lengths

### Integration Tests Needed
- Full user lifecycle (register → login → create project → add task → edit → drag)
- Multi-user scenarios (user A creates project, user B cannot see it)
- Logout/login cycles
- Data persistence across sessions

### E2E Tests Needed
- Browser drag/drop interaction
- Slider interaction
- Modal forms (edit task)
- Multi-user login/logout flows

---

## Success Criteria

- [ ] Edit task form works (create, open, save, cancel)
- [ ] Tasks persist immediately after creation
- [ ] Drag and drop functional (horizontal and vertical)
- [ ] User data properly isolated by user
- [ ] Users persist across logout/login cycles
- [ ] No demo data visible to new users
- [ ] 3-week slider implemented and functional
- [ ] All tests passing
- [ ] Deployed to production
- [ ] User testing confirms functionality

---

**Last Updated:** 2026-05-08
**Next Review:** After fixes applied

