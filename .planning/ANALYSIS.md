# Critical Defects Analysis & Fix Plan

## DEFECT 1: Missing Edit Task Functionality

### Root Cause
- Line 1274 in index.html: Task items only have a "Delete" button
- No edit button exists in the UI
- `editTask()` function is completely missing
- Edit modal HTML is not defined
- The form to populate existing task data does not exist

### Impact
Users cannot modify task details after creation. They must delete and recreate tasks.

### Fix Required
1. Add "Edit" button to task items (renderTasks function)
2. Create editTask() function to open modal
3. Create edit modal HTML in the UI
4. Populate modal with current task data
5. Implement save handler to call updateTask()

---

## DEFECT 2: Tasks Disappear After Addition (No Immediate Reflection)

### Root Cause
Looking at addTask() in index.html (line 1156):
- Line 1209: `loadProjects()` is called after adding task
- Line 1210: `selectProject(currentProjectId)` is called to re-render
- Line 1023: `renderProjectsList()` is called
- Line 1081: `renderTasks()` and `renderGantt()` should be called

**Issue**: The flow depends entirely on server correctly returning the new task in the projects list.

### Verification Needed
1. Check if server actually saves the task to database
2. Verify the task is returned in the response
3. Confirm renderGantt() is being called

### Fix Required
1. Debug the addTask POST to verify server response includes new task
2. Add console.log statements to trace execution
3. Ensure loadProjects() returns updated project data
4. Verify renderGantt() displays the new task

---

## DEFECT 3: Drag & Drop Not Working

### Root Cause Analysis

**Horizontal drag (date shift):**
- Lines 750-811: mousemove listener exists
- Line 751: Guard clause checks `!draggedBar || !dragStartX || !currentXScale || !currentTasks`
- **Issue at line 767**: `dayWidth = currentWidth / (currentMaxDate - currentMinDate) * 1000 * 60 * 60 * 24`
  - This assumes currentMaxDate and currentMinDate are Date objects
  - But the calculation is incorrect: dividing width by milliseconds
  - Should calculate days between dates, not use millisecond multiplication

**Vertical drag (reorder):**
- Lines 786-810: Reorder logic exists
- Line 788: `taskHeight = currentYScale.bandwidth() + currentYScale.padding() * currentYScale.bandwidth()`
  - This is incorrect: yScale.padding() returns a padding ratio (0-1), not a pixel value
  - Should be: `taskHeight = (currentYScale.bandwidth() + margin) / total_tasks`

**Global scale variables:**
- Lines 685-691: Global variables defined
- Line 1383: currentXScale is set in renderGantt
- Line 1391: currentYScale is set in renderGantt
- But currentHeight does not include the margin bottom calculation

### Verification
The grab cursor appears, but nothing happens when dragging because:
1. draggedBar is set by mousedown (line 1471)
2. Drag calculations are fundamentally broken
3. Scale variables may not be properly initialized

### Fix Required
1. Fix dayWidth calculation: `const dayWidth = currentWidth / countDays(currentMinDate, currentMaxDate)`
2. Fix taskHeight calculation for vertical drag
3. Verify scales are being stored correctly
4. Test both horizontal and vertical drag after fix

---

## DEFECT 4: Random Demo Data Persisted on User Switch

### Root Cause
**Possible causes:**
1. localStorage not cleared properly on logout
2. Demo data somehow exists in the database
3. Global `projects` array not properly reset when switching users
4. Server not properly filtering projects by owner

### Investigation
- Line 999: `projects = []` in logout() should clear demo data
- Line 446: Server filters by owner: `user_projects = [p for p in all_projects if p.get('owner') == username]`
- **No demo data generation code found** in the server

### Most Likely Cause
The projects array is being retained in browser memory when:
1. User A logs out (projects array cleared)
2. User A logs back in or User B logs in
3. If loadProjects() is called but fails or returns cached data

### Fix Required
1. Ensure logout() properly clears localStorage
2. Verify server user scoping is working
3. Clear browser localStorage completely on logout
4. Test with two different user accounts

---

## DEFECT 5: User Not Persisting (Re-registration Required)

### Root Cause Analysis

**Registration flow (lines 950-990):**
- Line 964: POST to `/api/auth/register`
- Line 523-526: Server executes: `INSERT INTO users (username, password) VALUES (?, ?)`
- Line 530: Server creates session token
- Returns token and username

**Login flow (lines 912-948):**
- Line 924: POST to `/api/auth/login`
- Line 568: Server executes: `SELECT username, password FROM users WHERE username = ?`
- Line 572: Verify password
- Line 578: Create session token

**Hypothesis:**
The registration IS saving to database (line 523-526 executes INSERT).
The login should work because SELECT runs on the same database.

### Most Likely Cause
1. SQLite database file is not persisting across server restarts
2. Database initialization is creating empty tables instead of reusing existing data
3. Multiple database connections aren't properly sharing data
4. Server is using in-memory database or temporary database

### Investigation
Line 15: `DB_FILE = 'task_gantt.db'` - should create persistent file
Line 71-84: `_init_sqlite_db()` uses `CREATE TABLE IF NOT EXISTS`

**Real issue**: If the server restarts or process reloads, in-memory sessions are cleared, but users should still be in the database.

### Fix Required
1. Verify database file is being created and persisted
2. Check if users table actually contains the registered user
3. Ensure database connection is reusing the same file
4. Test: Register user → logout → login with same credentials

---

## DEFECT 6: Feature Request - 3-Week Sliding Window

### Current State
- Gantt chart shows entire project timeline
- All dates rendered at once
- No way to navigate long projects

### Required Changes
1. Calculate current 3-week window (21 days)
2. Create horizontal slider component at bottom
3. Slider shows position in full timeline
4. Update xScale domain when slider moves
5. Re-render Gantt chart on slider change

### Implementation Strategy
1. Add slider HTML element
2. Calculate totalProjectDays from minDate to maxDate
3. Use D3 to create slider track and handle
4. Bind slider change to xScale domain update
5. Re-render Gantt when window moves

---

## Summary Table

| Defect | Type | Severity | Root Cause | Fix Complexity |
|--------|------|----------|-----------|-----------------|
| 1. Edit Task | Missing Feature | High | No edit button/modal/handler | Medium |
| 2. Task Reflection | Logic Bug | High | Server/client sync issue | Low-Medium |
| 3. Drag & Drop | Broken Feature | Critical | Math errors in drag calc | Medium |
| 4. Demo Data Leak | Security | Critical | Data isolation issue | Low |
| 5. User Persistence | Critical Bug | Critical | Database/session issue | Low-Medium |
| 6. 3-Week Slider | Feature Request | Medium | Not implemented | Medium |

