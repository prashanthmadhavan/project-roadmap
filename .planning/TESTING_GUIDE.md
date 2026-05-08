# Testing Guide - Task Gantt Chart Defect Fixes

This guide provides step-by-step instructions to verify each defect fix works correctly.

## Prerequisites

- Application server running (`python3 server.py`)
- Browser with access to http://localhost:5000
- Test user account (use demo/Demo@1234 or create a new one)

---

## DEFECT 1: Edit Task Functionality

### Test Scenario: Edit an existing task

**Setup:**
1. Login with any user account
2. Select or create a project with at least one task

**Test Steps:**
1. In the "Tasks" section on the left, click the **"Edit"** button on any task
   - **Expected:** Modal dialog appears with title "Edit Task"
   - **Expected:** Form contains current task data:
     - Task name field populated
     - Start date field populated
     - End date field populated

2. Modify the task name:
   - Clear the current name
   - Type a new name
   - **Expected:** Text updates in the input field

3. Modify the start date:
   - Click the start date field
   - Select a different date (earlier than current)
   - **Expected:** Date picker appears and updates

4. Click **"Save Changes"** button
   - **Expected:** Modal closes
   - **Expected:** Task list updates with new name
   - **Expected:** Gantt chart updates showing the task with new start date
   - **Expected:** Task bar position shifts to reflect new date range

5. Click "Edit" again on the same task
   - **Expected:** Form shows the updated values

### Test Scenario: Cancel without saving

1. Click "Edit" on a task
2. Modify the name
3. Click **"Cancel"** button
   - **Expected:** Modal closes
   - **Expected:** Task name remains unchanged in task list
   - **Expected:** Gantt chart shows original task bar position

### Test Scenario: Date validation

1. Click "Edit" on a task
2. Set end date earlier than start date
3. Click "Save Changes"
   - **Expected:** Alert appears: "Start date must be before end date"
   - **Expected:** Modal remains open

4. Set start date = end date
5. Click "Save Changes"
   - **Expected:** Alert appears: "Task must span at least one day"
   - **Expected:** Modal remains open

**Result:** ✅ PASS or ❌ FAIL - _____

---

## DEFECT 3: Drag & Drop Functionality

### Test Scenario A: Horizontal Drag (Shift Task Dates)

**Setup:**
1. Login and select a project with tasks
2. Create tasks with clear dates (e.g., Jan 1-5, Jan 8-12)

**Test Steps:**
1. **Locate a task bar** in the Gantt chart on the right
   - **Expected:** Cursor changes to "grab" cursor when hovering

2. **Click and drag RIGHT** (forward in time)
   - Click and hold on a task bar
   - Drag to the right approximately 100 pixels
   - Release mouse
   - **Expected:** Task bar moves to the right
   - **Expected:** Task dates shift forward by several days
   - **Expected:** Task duration remains the same (bar width unchanged)
   - **Expected:** In task list, dates update to show new range

3. **Verify persistence:**
   - Refresh the page (F5)
   - **Expected:** Task still shows shifted dates
   - **Expected:** Gantt chart shows bar in new position

4. **Drag LEFT** (backward in time) on a different task
   - Click and hold on another task bar
   - Drag to the left approximately 50 pixels
   - Release mouse
   - **Expected:** Task bar moves to the left
   - **Expected:** Task dates shift backward
   - **Expected:** Bar position updates in Gantt chart

### Test Scenario B: Vertical Drag (Reorder Tasks)

**Setup:**
1. Same as above - project with multiple tasks

**Test Steps:**
1. **Click and drag task UP** (toward top of Gantt)
   - Click and hold on a task bar in the middle
   - Drag upward approximately 60 pixels
   - Release mouse
   - **Expected:** Task bar moves to a higher row
   - **Expected:** Task order changes in the task list
   - **Expected:** Task label on left side moves to new position

2. **Drag task DOWN** (toward bottom)
   - Click and hold on a task bar
   - Drag downward approximately 100 pixels
   - Release mouse
   - **Expected:** Task bar moves to a lower row
   - **Expected:** Task list reorders
   - **Expected:** Gantt chart reorders rows

3. **Verify reorder persists:**
   - Refresh page
   - **Expected:** Tasks remain in new order
   - **Expected:** Gantt rows match task list order

### Test Scenario C: Drag Visual Feedback

1. Start dragging a task bar
   - **Expected:** Task bar opacity decreases (becomes translucent)
   - **Expected:** Cursor changes to "grabbing"

2. Release the drag
   - **Expected:** Opacity returns to normal
   - **Expected:** Cursor returns to normal

**Result:** ✅ PASS or ❌ FAIL - _____

---

## DEFECT 4: Data Isolation on User Switch

### Test Scenario: Create User A and User B

**Setup:**
1. Open incognito/private browser window to avoid session caching
2. Or use two different browsers

**Test Steps:**
1. **Register User A:**
   - Click "Create one" on login page
   - Username: `testuser_a`
   - Password: `TestUser@123`
   - Click "Create Account"
   - **Expected:** Logged in as testuser_a

2. **Create projects and tasks for User A:**
   - Create a project named "User A Project"
   - Add 2-3 tasks
   - **Expected:** Tasks appear in sidebar and Gantt chart

3. **Logout User A:**
   - Click "Logout" button (top right)
   - **Expected:** Redirected to login page
   - **Expected:** All project data disappears
   - **Expected:** No projects visible in the sidebar
   - **Expected:** Gantt chart shows empty state

4. **Register/Login as User B:**
   - If first time: Click "Create one"
   - Username: `testuser_b`
   - Password: `TestUser@456`
   - Click "Create Account" or "Sign In"
   - **Expected:** Logged in as testuser_b

5. **Verify User B has different data:**
   - **Expected:** NO "User A Project" visible
   - **Expected:** Task list is empty (or shows only User B's tasks)
   - **Expected:** Gantt chart is empty
   - **Expected:** Can create own project without seeing User A's data

6. **Create Project for User B:**
   - Create a project named "User B Project"
   - Add 1-2 tasks
   - **Expected:** New project appears only for User B

7. **Logout User B and login as User A:**
   - Click Logout
   - Go to Login
   - Login with: `testuser_a` / `TestUser@123`
   - **Expected:** "User A Project" appears (User B's project NOT visible)
   - **Expected:** Original User A tasks are intact

8. **Test demo data isolation:**
   - Logout User A
   - Login as demo / Demo@1234
   - **Expected:** See demo projects only
   - **Expected:** No User A or User B projects visible

**Result:** ✅ PASS or ❌ FAIL - _____

---

## DEFECT 5: User Persistence (Already Working)

### Quick Verification Test

**Setup:**
1. Create a test account (if not already done)
   - Username: `persistence_test`
   - Password: `PersistTest@123`

**Test Steps:**
1. Login with persistence_test account
2. Create a project "Test Project"
3. Add a task "Test Task"
4. **Logout** (don't close browser)
5. **Wait** 5 seconds
6. **Login again** with same credentials: `persistence_test` / `PersistTest@123`
   - **Expected:** Successfully logs in
   - **Expected:** "Test Project" appears
   - **Expected:** "Test Task" is visible with correct dates

7. **Verify data persists:**
   - Close browser completely
   - Open browser again
   - Go to localhost:5000
   - Login with persistence_test
   - **Expected:** Same projects and tasks appear
   - **Expected:** All data is intact

**Result:** ✅ PASS or ❌ FAIL - _____

---

## FEATURE: 3-Week Timeline Slider

### Test Scenario: Slider appears for long projects

**Setup:**
1. Login with any account
2. Create a project named "Long Project"

**Test Steps:**
1. **Add multiple tasks spanning > 21 days:**
   - Task 1: Jan 1 - Jan 10
   - Task 2: Jan 15 - Jan 25
   - Task 3: Feb 1 - Feb 5
   - **Total span:** ~36 days

2. **Select the project:**
   - Click on "Long Project" in sidebar
   - **Expected:** Gantt chart renders with all tasks
   - **Expected:** **Timeline slider appears** below Gantt chart
   - **Expected:** Slider shows label "📅 Timeline Navigation (3-week window)"
   - **Expected:** Slider shows date range (e.g., "Jan 01 → Jan 22")

3. **Test slider interaction:**
   - **Drag the slider** to the right
   - **Expected:** Date range updates in real-time
   - **Expected:** Start date advances by days shown on slider

4. **Click on slider track:**
   - Click near the right end of the slider
   - **Expected:** Slider handle jumps to that position
   - **Expected:** Date range updates

### Test Scenario: Slider hidden for short projects

**Test Steps:**
1. **Create a short project:**
   - Create "Short Project"
   - Add task: Jan 1 - Jan 15 (14 days)
   - Select project

2. **Verify slider is hidden:**
   - **Expected:** Gantt chart renders normally
   - **Expected:** **No timeline slider appears** below chart
   - **Expected:** This is correct behavior (UX optimization)

### Test Scenario: Slider date formatting

**Test Steps:**
1. With "Long Project" selected
2. Observe date display in slider
   - **Expected:** Format is "MonAbb DD → MonAbb DD"
   - **Expected:** Example: "Jan 01 → Jan 22"
   - **Expected:** Always shows exactly 21-day windows

**Result:** ✅ PASS or ❌ FAIL - _____

---

## Integration Test: Full Workflow

**Setup:** Fresh browser, no accounts

**Workflow:**
1. **Register new user:** `workflow_test` / `WorkflowTest@123`
2. **Create project:** "Workflow Test Project"
3. **Add 3 tasks** with different dates:
   - Task A: Jan 5 - Jan 10
   - Task B: Jan 15 - Jan 20  
   - Task C: Feb 1 - Feb 5
4. **Edit Task A:**
   - Change name to "Task A Edited"
   - Change start to Jan 6
   - Save
   - Verify change in list and chart
5. **Drag Task B horizontally:**
   - Shift dates forward 1 week
   - Release
   - Verify dates updated
6. **Drag Task C vertically:**
   - Move to top position
   - Verify reorder in list
7. **Verify timeline slider:**
   - Project > 21 days, so slider should appear
   - Drag slider to middle
   - Dates update correctly
8. **Logout and login:**
   - Logout
   - Login again
   - Verify all changes persisted

**Result:** ✅ PASS or ❌ FAIL - _____

---

## Browser Compatibility Testing

Test on these browsers (if available):

- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iPad/iPhone)
- [ ] Chrome Mobile (Android)

**Known Issues:**
- Slider styling may vary slightly on Safari (native range input styling)
- Modal may need scrolling on small screens
- Drag may feel different on touch devices

---

## Test Results Summary

| Test | Result | Notes |
|------|--------|-------|
| DEFECT 1: Edit Task | ⬜ | |
| DEFECT 3: Drag & Drop - Horizontal | ⬜ | |
| DEFECT 3: Drag & Drop - Vertical | ⬜ | |
| DEFECT 4: Data Isolation | ⬜ | |
| DEFECT 5: User Persistence | ⬜ | |
| FEATURE: Timeline Slider | ⬜ | |
| Integration Test | ⬜ | |

**Legend:** ✅ PASS | ❌ FAIL | ⬜ NOT TESTED

---

## Troubleshooting

### Edit Modal doesn't appear
- Check browser console for errors (F12 → Console)
- Verify JavaScript is enabled
- Hard refresh page (Ctrl+Shift+R or Cmd+Shift+R)

### Drag doesn't work
- Ensure you're clicking on the task bar itself (not the text)
- Try longer drag (minimum 5 pixels required to trigger)
- Check console for any drag-related errors
- Verify currentXScale is not null (check with console logs)

### Slider doesn't appear
- Verify project has tasks spanning > 21 days
- Check date format (should be YYYY-MM-DD)
- Refresh page
- Check that tasks are properly loaded

### Data isolation not working
- Clear browser localStorage (Dev Tools → Application)
- Logout and ensure all cookies are cleared
- Test in incognito/private window
- Check server logs for SQL errors

### User persistence fails
- Verify SQLite database exists: `task_gantt.db`
- Check database has users table: `sqlite3 task_gantt.db "SELECT name FROM sqlite_master WHERE type='table';"`
- Verify user was inserted: `sqlite3 task_gantt.db "SELECT username FROM users;"`
- Check server logs for database errors

---

## Sign-off

**Tester Name:** ___________________  
**Date:** ___________________  
**Result:** ⬜ All Tests Passed | ⬜ Some Tests Failed | ⬜ Unable to Test

**Comments:**
```
[Space for notes and observations]
```

