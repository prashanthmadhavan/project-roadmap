---
phase: 1
depth: standard
reviewed: 2026-05-08T00:00:00Z
files_reviewed: 2
files_reviewed_list:
  - index.html
  - server.py
findings:
  critical: 6
  warning: 8
  info: 10
  total: 24
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-05-08
**Depth:** standard (per-file analysis with language-specific checks)
**Files Reviewed:** 2
**Status:** Issues Found

## Executive Summary

The Task Gantt Chart application has a **solid foundation** with proper parameterized SQL queries and session management infrastructure. However, **6 critical security and logic issues** have been identified that must be fixed before production deployment:

1. **XSS vulnerability in dynamic HTML rendering** (inline task deletion)
2. **Race condition in drag-and-drop updates** (unsynchronized state mutations)
3. **Missing input validation** on form submissions (empty date ranges, negative spans)
4. **Unsafe dependencies parsing** (bare `except:` catches)
5. **Missing CSRF protection** (stateless token validation only)
6. **Information disclosure in error messages** (leaks internal state)

Additionally, **8 warnings** address error handling gaps, logic errors, and performance concerns. The codebase would benefit from **refactoring** large functions (renderGantt is 240+ lines) and stricter input validation on the frontend.

---

## Critical Issues

### CR-01: XSS Vulnerability in Task Deletion via Event Handler

**File:** `index.html:1099`
**Severity:** CRITICAL
**Category:** Security

**Issue:**
The `removeDependency` function in inline onclick handlers embeds task IDs directly into HTML without proper escaping. While task IDs are currently numeric timestamps, unsanitized task names in similar patterns (line 1171) could be exploited.

More critically, the task deletion button at line 1196 uses `onclick="deleteTask('${task.id}')"` which creates an **XSS risk** if task IDs contain special characters or quotes. A malicious actor could craft a task ID containing JavaScript code (if the API doesn't validate strictly) that would execute in the context of the user's browser.

**Current Code:**
```javascript
// Line 1099 - onclick directly embeds task ID
<button onclick="removeDependency('${depId}')">Remove</button>

// Line 1196 - similar pattern with task deletion
<button class="delete-btn" onclick="deleteTask('${task.id}')">Delete</button>
```

**Impact:**
- **XSS execution** if task IDs or names contain malicious scripts
- Attackers could steal auth tokens from localStorage
- Session hijacking is possible
- User could unknowingly perform unauthorized actions

**Recommended Fix:**
Replace inline event handlers with proper event delegation:

```javascript
function renderTasks() {
    if (!currentProjectId) {
        document.getElementById('tasksList').innerHTML = '';
        return;
    }

    const project = projects.find(p => p.id === currentProjectId);
    if (!project) return;

    const container = document.getElementById('tasksList');
    container.innerHTML = project.tasks.map(task => {
        const start = new Date(task.startDate).toLocaleDateString();
        const end = new Date(task.endDate).toLocaleDateString();
        return `
            <div class="task-item" data-task-id="${task.id}">
                <strong>${escapeHtml(task.name)}</strong><br>
                <small>${start} → ${end}</small>
                <div class="task-item-actions">
                    <button class="delete-btn" data-action="delete-task">Delete</button>
                </div>
            </div>
        `;
    }).join('');

    // Add event listener for delegation
    container.addEventListener('click', (e) => {
        if (e.target.getAttribute('data-action') === 'delete-task') {
            const taskId = e.target.closest('[data-task-id]').dataset.taskId;
            deleteTask(taskId);
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

---

### CR-02: Race Condition in Drag-and-Drop Task Updates

**File:** `index.html:747-764`
**Severity:** CRITICAL
**Category:** Bug

**Issue:**
The horizontal drag handler updates `draggedBar` object properties directly (lines 754-761) **without locking** or preventing concurrent updates. When a user drags a task while the server is processing a previous update, multiple conflicting updates are sent:

1. User drags task → updates `draggedBar.startDate` locally
2. Server is processing previous drag → sends conflicting dates back
3. `loadProjects()` overwrites local changes
4. Data corruption or task jumping between dates

The `dragStartX` is updated on line 763 but only AFTER the update. Between the `updateTask` call (line 764) and server response, the UI can accept new drag events that create a race condition.

**Current Code:**
```javascript
// Line 754-764: Direct mutation without synchronization
startDate.setDate(startDate.getDate() + daysShifted);
endDate.setDate(endDate.getDate() + daysShifted);

draggedBar.startDate = startDate.toISOString().split('T')[0];
draggedBar.endDate = endDate.toISOString().split('T')[0];

dragStartX = event.clientX;
updateTask(draggedBar.id, draggedBar);  // Async call!
```

**Impact:**
- **Data corruption**: Multiple updates can overwrite each other
- **Inconsistent UI state**: User sees task at position A but server has it at position B
- **Lost user work**: If two drags happen quickly, second drag data is lost
- **Poor UX**: Janky animation, unexpected task jumps after drop

**Recommended Fix:**
Implement an **update queue** and **lock** mechanism:

```javascript
let isUpdatingTask = false;
let pendingTaskUpdate = null;

document.addEventListener('mousemove', async (event) => {
    if (!draggedBar || !dragStartX || !currentXScale || !currentTasks) return;

    const deltaX = event.clientX - dragStartX;
    const deltaY = event.clientY - dragStartY;
    
    if (!dragMode) {
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 5) {
            dragMode = 'horizontal';
        } else if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > 5) {
            dragMode = 'vertical';
        }
    }
    
    if (dragMode === 'horizontal') {
        const dayWidth = currentWidth / (currentMaxDate - currentMinDate) * 1000 * 60 * 60 * 24;
        const daysShifted = Math.round(deltaX / dayWidth);

        if (daysShifted === 0) return;

        const startDate = new Date(draggedBar.startDate);
        const endDate = new Date(draggedBar.endDate);
        
        startDate.setDate(startDate.getDate() + daysShifted);
        endDate.setDate(endDate.getDate() + daysShifted);

        draggedBar.startDate = startDate.toISOString().split('T')[0];
        draggedBar.endDate = endDate.toISOString().split('T')[0];
        
        dragStartX = event.clientX;
        
        // Queue update instead of sending immediately
        pendingTaskUpdate = { id: draggedBar.id, data: draggedBar };
    }
});

document.addEventListener('mouseup', async () => {
    if (draggedBar && pendingTaskUpdate && !isUpdatingTask) {
        isUpdatingTask = true;
        try {
            await updateTask(pendingTaskUpdate.id, pendingTaskUpdate.data);
        } finally {
            isUpdatingTask = false;
        }
    }
    draggedBar = null;
    dragStartX = null;
    dragStartY = null;
    dragMode = null;
    pendingTaskUpdate = null;
});
```

---

### CR-03: Missing Input Validation - Date Range Logic Error

**File:** `index.html:1105-1119`
**Severity:** CRITICAL
**Category:** Bug

**Issue:**
The `addTask()` function does **not validate** that `startDate < endDate`. A user can create tasks with end dates **before** start dates, or with identical dates. This breaks Gantt chart rendering logic (line 1248-1249 which uses `Math.min` and `Math.max` on dates).

Additionally, there is **no validation** for empty date fields on the client side despite being required. If a user submits with empty dates, the server receives `undefined` values which get stored as invalid dates in the database.

**Current Code:**
```javascript
// Line 1116-1119: No date range validation
if (!name || !startDate || !endDate) {
    alert('Please fill in all fields');
    return;
}
// NO CHECK: startDate < endDate
```

**Impact:**
- **Invalid data in database**: Tasks with endDate < startDate
- **Gantt chart rendering errors**: min/max date logic fails
- **Drag-and-drop bugs**: Timeline calculations use invalid dates
- **Data integrity violation**: Business logic assumes endDate >= startDate

**Recommended Fix:**
Add client-side validation:

```javascript
async function addTask() {
    if (!currentProjectId) {
        alert('Please select a project first');
        return;
    }

    const name = document.getElementById('taskName').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const dependencyId = document.getElementById('dependencySelect').value;

    if (!name || !startDate || !endDate) {
        alert('Please fill in all fields');
        return;
    }

    // Validate date range
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (start > end) {
        alert('Start date must be before end date');
        return;
    }

    if (start.getTime() === end.getTime()) {
        alert('Task must span at least one day');
        return;
    }

    // Rest of function...
}
```

---

### CR-04: Unsafe Exception Handling in normalize_task()

**File:** `server.py:274-277`
**Severity:** CRITICAL
**Category:** Security / Quality

**Issue:**
The bare `except:` clause on line 276 **silently swallows ALL exceptions** when parsing dependencies JSON. This includes:
- `KeyboardInterrupt` (user presses Ctrl+C, but app continues silently)
- `SystemExit` (program should exit, but continues)
- `MemoryError` (system running out of memory, masked)
- Genuine `json.JSONDecodeError` that should be logged

This is a **severe anti-pattern** in Python. If dependencies contain malformed JSON, the error is silently caught and replaced with `[]`. An attacker could craft tasks with specially formatted dependency strings to trigger unexpected behavior.

**Current Code:**
```python
# Line 273-277
if isinstance(normalized['dependencies'], str):
    try:
        normalized['dependencies'] = json.loads(normalized['dependencies'])
    except:  # TOO BROAD - catches EVERYTHING
        normalized['dependencies'] = []
```

**Impact:**
- **Silent failures**: Malformed data is silently replaced without logging
- **Debugging nightmare**: Errors are hidden, making root cause analysis impossible
- **Security risk**: Attackers can exploit by sending crafted dependencies
- **Data loss**: Legitimate dependencies are discarded without notification

**Recommended Fix:**
Catch specific exception types and log errors:

```python
if isinstance(normalized['dependencies'], str):
    try:
        normalized['dependencies'] = json.loads(normalized['dependencies'])
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse dependencies for task {task.get('id')}: {e}")
        normalized['dependencies'] = []
    except Exception as e:
        print(f"Unexpected error parsing dependencies: {e}")
        raise  # Re-raise unexpected exceptions
```

---

### CR-05: CORS Configuration Allows Any Origin - Missing CSRF Protection

**File:** `server.py:391` (and all endpoints)
**Severity:** CRITICAL
**Category:** Security

**Issue:**
Every API response includes `'Access-Control-Allow-Origin': '*'` (line 391), which allows **ANY domain** to make requests to this API. Combined with **no CSRF token validation**, an attacker can:

1. Host a malicious website at `evil.com`
2. User visits `evil.com` while logged into `app.com`
3. JavaScript on `evil.com` sends: `fetch('/api/projects/delete', {method: 'DELETE'})`
4. Browser automatically includes the user's auth token from localStorage
5. Project is deleted without user's knowledge

**The root cause**: Tokens are stored in `localStorage` (line 905 in index.html), which is **accessible to any JavaScript on the page**, including malicious scripts from CORS requests.

**Current Code:**
```python
# Line 390-391: Allows any origin
self.send_header('Access-Control-Allow-Origin', '*')

# Line 818 in index.html: Token in localStorage
localStorage.setItem('authToken', authToken);
```

**Impact:**
- **CSRF attacks**: Attacker can perform actions as the authenticated user
- **Cross-site request forgery**: DELETE /projects/<id> can be triggered from any site
- **Session hijacking via token theft**: Malicious JavaScript can read localStorage
- **Compliance violation**: OWASP A01:2021 – Broken Access Control

**Recommended Fix:**

1. **Restrict CORS to specific origin:**
```python
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', 'http://localhost:5000')

# In send_json():
self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGIN)
```

2. **Move token to httpOnly cookie (prevents JavaScript access):**
```javascript
// In login() function - DON'T store in localStorage
// Instead, server sets httpOnly cookie in response
// Browser automatically includes it in requests
```

3. **Add CSRF token validation on server side:**
```python
def do_POST(self):
    # For state-changing requests (POST, PUT, DELETE)
    csrf_token = self.headers.get('X-CSRF-Token', '')
    if not csrf_token or csrf_token not in valid_csrf_tokens:
        self.send_json(403, {'error': 'CSRF token missing or invalid'})
        return
```

---

### CR-06: Bare Except Clause in Password Verification

**File:** `server.py:370`
**Severity:** CRITICAL
**Category:** Security / Quality

**Issue:**
Similar to CR-04, the `verify_password()` function uses a bare `except:` clause that silently swallows all exceptions during password verification. This is dangerous because:

1. If the password hash is corrupted or malformed, the function returns `False` instead of raising an error
2. If there's a system error (OutOfMemory, etc.), it silently fails
3. An attacker could craft a malicious password hash that causes an exception, which would silently fail and be treated as "password doesn't match"
4. Makes debugging authentication issues extremely difficult

**Current Code:**
```python
# Line 364-371
def verify_password(self, password, hashed):
    """Verify password against hash"""
    try:
        salt, hash_hex = hashed.split('$')
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_hex == hash_obj.hex()
    except:
        return False
```

**Impact:**
- **Silent security errors**: Malformed hashes silently fail instead of being reported
- **Debugging nightmare**: Authentication failures are hard to diagnose
- **Attack surface**: Attackers could trigger exceptions to bypass authentication
- **Data integrity**: No indication that stored hash is corrupted

**Recommended Fix:**
```python
def verify_password(self, password, hashed):
    """Verify password against hash"""
    try:
        parts = hashed.split('$')
        if len(parts) != 2:
            print(f"Warning: Invalid password hash format (expected 2 parts, got {len(parts)})")
            return False
        
        salt, hash_hex = parts
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_hex == hash_obj.hex()
    except ValueError as e:
        print(f"Error verifying password: Invalid hash format - {e}")
        return False
    except Exception as e:
        print(f"Critical error during password verification: {e}")
        raise  # Re-raise unexpected errors
```

---

## Warning Issues

### WR-01: Missing Error Handling for Network Failures

**File:** `index.html:978-991`
**Severity:** WARNING
**Category:** Bug / Quality

**Issue:**
The `loadProjects()` function calls `loadProjects()` but its own error handler at line 989 only logs errors without notifying the user. If the API is unavailable, the user sees:
- Empty projects list
- No error message
- No indication anything went wrong
- No retry mechanism

This creates a poor UX and makes debugging difficult.

**Current Code:**
```javascript
async function loadProjects() {
    try {
        const response = await fetch('/api/projects', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        projects = await response.json() || [];
        renderProjectsList();
        if (projects.length > 0 && !currentProjectId) {
            selectProject(projects[0].id);
        }
    } catch (error) {
        console.error('Error loading projects:', error);  // Only logs, no user feedback
    }
}
```

**Impact:**
- **Silent failures**: User doesn't know data didn't load
- **Confusion**: Empty list could mean "no projects" or "network error"
- **No retry option**: User must manually refresh page
- **Data loss perception**: User might think they deleted a project when it was just a load error

**Recommended Fix:**
```javascript
async function loadProjects() {
    try {
        const response = await fetch('/api/projects', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        projects = await response.json() || [];
        renderProjectsList();
        if (projects.length > 0 && !currentProjectId) {
            selectProject(projects[0].id);
        }
    } catch (error) {
        console.error('Error loading projects:', error);
        // Show error to user
        alert('Failed to load projects. Please check your connection and refresh.');
    }
}
```

---

### WR-02: Undefined Element Reference in renderDependenciesDisplay()

**File:** `index.html:1090`
**Severity:** WARNING
**Category:** Bug

**Issue:**
The `updateDependenciesDisplay()` function tries to access `document.getElementById('dependenciesList')` (line 1090), but this element is **never defined in the HTML**. The function was written for a feature that was planned but not implemented.

This causes:
- `container` is `null`
- Any attempt to set `container.innerHTML` throws a TypeError
- The entire UI breaks when dependencies are managed

**Current Code:**
```javascript
// Line 1090: Element doesn't exist in HTML
const container = document.getElementById('dependenciesList');

if (!project) return;

container.innerHTML = currentDependencies.map(...).join('');  // TypeError!
```

**HTML:** No `<div id="dependenciesList">` anywhere in the document.

**Impact:**
- **Runtime error**: TypeError when managing dependencies
- **UI breakage**: Application crashes when trying to add/remove dependencies
- **Lost functionality**: Dependency management feature doesn't work
- **Bad UX**: User can't manage task dependencies properly

**Recommended Fix:**
Either implement the dependencies list HTML:

```html
<!-- Add to sidebar in HTML -->
<div class="sidebar-section" id="dependenciesSectionNew" style="display: none;">
    <h2>Dependencies</h2>
    <div id="dependenciesList" class="dependencies-list"></div>
</div>
```

Or remove the unused code if dependencies will be managed differently:

```javascript
function updateDependenciesDisplay() {
    // Feature not yet implemented
    // Dependencies are currently selected via dropdown in addTask()
}
```

---

### WR-03: Unchecked Array Access in Drag Calculation

**File:** `index.html:1248-1249`
**Severity:** WARNING
**Category:** Bug

**Issue:**
The `renderGantt()` function calculates `minDate` and `maxDate` using `Math.min/max` on an empty array without validation. If a project has **no tasks**, the calculation produces `Infinity` and `-Infinity`:

```javascript
// Line 1247-1249
const dates = tasks.flatMap(t => [new Date(t.startDate), new Date(t.endDate)]);
const minDate = new Date(Math.min(...dates));  // If dates is empty: Math.min() = Infinity
const maxDate = new Date(Math.max(...dates));  // If dates is empty: Math.max() = -Infinity
```

While line 1241 checks for `project.tasks.length === 0`, this check happens AFTER the variable assignment. However, if this code is refactored later, the bug could resurface.

**Current Code:**
```javascript
const tasks = project.tasks;
const dates = tasks.flatMap(t => [new Date(t.startDate), new Date(t.endDate)]);
const minDate = new Date(Math.min(...dates));  // Breaks if tasks is empty!
const maxDate = new Date(Math.max(...dates));
```

**Impact:**
- **Math errors**: NaN propagates through date calculations
- **Rendering failure**: SVG coordinates become NaN
- **Gantt chart breaks**: Timeline doesn't display properly
- **Hard to debug**: Error is subtle, only appears with empty projects

**Recommended Fix:**
Add explicit validation:

```javascript
const tasks = project.tasks;

// Early return if no tasks (cleaner check)
if (!tasks || tasks.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>📋 No tasks. Add a task to see the Gantt chart.</p></div>';
    return;
}

const dates = tasks.flatMap(t => [new Date(t.startDate), new Date(t.endDate)]);
const minDate = new Date(Math.min(...dates));
const maxDate = new Date(Math.max(...dates));
```

---

### WR-04: Missing Response Status Check in addTask()

**File:** `index.html:1139`
**Severity:** WARNING
**Category:** Bug

**Issue:**
The `addTask()` function checks `if (response.ok)` on line 1139, but the error case has **no handler**. If the server returns 400 (invalid data) or 500 (server error), the function silently fails:

```javascript
if (response.ok) {
    // Clear form and reload
    document.getElementById('taskName').value = '';
    // ...
}
// No else clause - error is silent!
```

The user clears the form, but the task wasn't created. They have no indication of failure.

**Current Code:**
```javascript
if (response.ok) {
    document.getElementById('taskName').value = '';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('dependencySelect').value = '';
    loadProjects();
    selectProject(currentProjectId);
}
// Missing error handling
```

**Impact:**
- **Silent failures**: Task creation fails but user isn't notified
- **Data loss illusion**: Form is cleared even if creation failed
- **Confusion**: User thinks task was created when it wasn't
- **Debugging difficulty**: No error message to indicate what went wrong

**Recommended Fix:**
```javascript
if (response.ok) {
    document.getElementById('taskName').value = '';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('dependencySelect').value = '';
    loadProjects();
    selectProject(currentProjectId);
} else {
    const error = await response.json();
    alert(`Failed to add task: ${error.error || 'Unknown error'}`);
}
```

---

### WR-05: Off-by-One Error in Weekday Counting

**File:** `index.html:1204-1215`
**Severity:** WARNING
**Category:** Logic Error

**Issue:**
The `countWeekdays()` function iterates with `while (current <= end)` (line 1207), which **includes the end date** in the count. This means:
- Task from Monday to Monday (1 day) counts as 2 days
- Task spanning 5 calendar days (Mon-Fri) counts as 5 days (should be 5)

However, if the end date is a Saturday, it counts the weekend day, violating the "weekdays only" logic. The issue is subtle: the loop includes the end date, which may or may not be a weekday.

**Current Code:**
```javascript
// Line 1204-1215
function countWeekdays(start, end) {
    let count = 0;
    const current = new Date(start);
    while (current <= end) {  // <= includes end date
        const dayOfWeek = current.getDay();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            count++;
        }
        current.setDate(current.getDate() + 1);
    }
    return count;
}
```

**Impact:**
- **Off-by-one in Gantt calculation**: Timeline coordinates are slightly off
- **Visual misalignment**: Bars don't align with dates in some cases
- **Drag-drop precision**: Date shifts are off by a day
- **Business logic error**: Task duration calculations are incorrect

**Recommended Fix:**
```javascript
function countWeekdays(start, end) {
    let count = 0;
    const current = new Date(start);
    while (current < end) {  // < excludes end date (standard practice)
        const dayOfWeek = current.getDay();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            count++;
        }
        current.setDate(current.getDate() + 1);
    }
    return count;
}
```

Or add a comment explaining why `<=` is used:

```javascript
function countWeekdays(start, end) {
    // Note: includes end date to count it as a full day
    // Task from Mon to Mon = 2 weekdays
    let count = 0;
    const current = new Date(start);
    while (current <= end) {
        const dayOfWeek = current.getDay();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) {
            count++;
        }
        current.setDate(current.getDate() + 1);
    }
    return count;
}
```

---

### WR-06: Unvalidated User Input in Project Creation

**File:** `server.py:582`
**Severity:** WARNING
**Category:** Security

**Issue:**
While the server validates username and password thoroughly in `do_POST` registration/login, the **project creation endpoint does NOT validate**:
- Project name can be empty or null
- Description length is unchecked (could be extremely long)
- No check for duplicate project names for the same user
- SQL injection risk if the project name contains special characters (though parameterized queries help)

**Current Code:**
```python
# Line 582: No validation of project data
(project_id, username, data.get('name'), data.get('description', ''))
```

**Impact:**
- **Malformed data**: Projects with empty names stored in database
- **Spam/abuse**: Users could create projects with 1MB descriptions
- **Data duplication**: Multiple projects with same name cause confusion
- **Database bloat**: Unbounded data could fill up disk

**Recommended Fix:**
```python
# In do_POST, for project creation:
try:
    data = json.loads(body)
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    # Validate name
    if not name:
        self.send_json(400, {'error': 'Project name is required'})
        return
    
    if len(name) > 255:
        self.send_json(400, {'error': 'Project name is too long (max 255 characters)'})
        return
    
    if len(description) > 1000:
        self.send_json(400, {'error': 'Description is too long (max 1000 characters)'})
        return
    
    # Rest of project creation...
```

---

### WR-07: Memory Leak - Event Listeners Not Cleaned Up on Tab Switch

**File:** `index.html:603-609`
**Severity:** WARNING
**Category:** Performance / Quality

**Issue:**
The `switchProjectTab()` function at line 1501 does not clean up event listeners from the previous tab's content. Each time a user switches tabs, new listeners are added but old ones remain, causing:

1. Multiple event handlers on the same elements
2. Memory accumulation as the app runs
3. Duplicate events firing (event fires multiple times)

Additionally, the task list rendering in `renderTasks()` (line 1188) creates new event listeners each time a project is selected without removing old ones.

**Current Code:**
```javascript
// Line 1501-1512: Only removes active class, doesn't clean up listeners
function switchProjectTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    
    event.target.classList.add('active');
    
    if (tab === 'projects') {
        document.getElementById('projectsTab').classList.add('active');
    } else {
        document.getElementById('newProjectTab').classList.add('active');
    }
}
```

**Impact:**
- **Memory leaks**: Listeners accumulate, memory usage grows over time
- **Duplicate event fires**: Clicking delete button fires delete multiple times
- **Performance degradation**: App gets slower as user uses it
- **Event handler bloat**: Hundreds of listeners attached after heavy use

**Recommended Fix:**
Use event delegation (single listener on container) instead of listeners on each element:

```javascript
// Single event listener for all project actions
const projectsList = document.getElementById('projectsList');
projectsList.addEventListener('click', (e) => {
    const projectItem = e.target.closest('.project-item');
    if (projectItem) {
        const projectId = projectItem.dataset.projectId;
        selectProject(projectId);
    }
});

// When rendering projects, add data attributes instead of inline handlers
function renderProjectsList() {
    const container = document.getElementById('projectsList');
    container.innerHTML = projects.map(project => `
        <div class="project-item ${project.id === currentProjectId ? 'active' : ''}" 
             data-project-id="${project.id}">
            <div class="project-item-name">${project.name}</div>
            <div class="project-item-count">${project.tasks.length} tasks</div>
        </div>
    `).join('');
}
```

---

### WR-08: Session Management - No Activity Tracking on Silent API Calls

**File:** `index.html:810-813 and throughout`
**Severity:** WARNING
**Category:** Security

**Issue:**
The session monitor (line 706) resets the timeout on user **input events** (mousedown, keydown, click, scroll, touchstart), but **not on API responses**. This means:

1. User is idle for 14 minutes (within 15-minute timeout)
2. Drag operation triggers an API call to update task
3. User is notified at 13 minutes that session will expire
4. User closes their laptop at 13:30 and comes back at 14:30 (1 hour later)
5. Session was already expired at 15 minutes, but code never checked

More critically, if the user is **actively making API calls** but not moving the mouse/keyboard (e.g., reading the chart while server operations happen), they could get timed out prematurely.

**Current Code:**
```javascript
// Line 725-729: Only tracks user input, not API activity
document.addEventListener('mousedown', resetSessionTimer);
document.addEventListener('keydown', resetSessionTimer);
document.addEventListener('click', resetSessionTimer);
document.addEventListener('scroll', resetSessionTimer);
document.addEventListener('touchstart', resetSessionTimer);
```

**Impact:**
- **Session timeout confusion**: User loses session without clear reason
- **Lost work**: Long-running operations (loading projects) trigger timeout
- **UX frustration**: User thinks they're active but session expired
- **Security gap**: Timeout isn't based on actual application usage

**Recommended Fix:**
Reset session timer on API responses:

```javascript
function resetSessionTimer() {
    lastActivityTime = Date.now();
    sessionWarningShown = false;
}

// Wrap all API calls to track activity
async function apiCall(url, options = {}) {
    resetSessionTimer();  // Mark activity when API call starts
    const response = await fetch(url, options);
    resetSessionTimer();  // Mark activity when API response received
    return response;
}

// Use wrapped API call everywhere:
const response = await apiCall('/api/projects', {
    headers: { 'Authorization': `Bearer ${authToken}` }
});
```

---

## Info Issues

### IF-01: Magic Numbers Should Be Named Constants

**File:** `index.html:691, 710, 721, 767, 749, 1261`
**Severity:** INFO
**Category:** Code Quality

**Issue:**
The code contains multiple hardcoded numeric values that should be extracted as named constants:
- `15 * 60 * 1000` (Session timeout, appears multiple times)
- `13 * 60 * 1000` (Warning threshold)
- `60000` (Session check interval)
- `5` (Drag sensitivity threshold)
- `1000 * 60 * 60 * 24` (Milliseconds per day)
- `50` (Task row height)
- `100` (Minimum bar width)
- `400` (Minimum chart height)

**Current Code:**
```javascript
const SESSION_TIMEOUT = 15 * 60 * 1000;  // Already a constant
if (timeSinceLastActivity > 13 * 60 * 1000 && !sessionWarningShown) {  // Magic number
    // ...
}, 60000);  // Magic number - interval
```

**Impact:**
- **Maintainability**: Changing session timeout requires finding all instances
- **Readability**: Unclear what `5` represents in drag handler
- **Consistency**: Different values used in different places for same concept
- **Testing**: Harder to test different configurations

**Recommended Fix:**
```javascript
// At top of script, near SESSION_TIMEOUT
const SESSION_TIMEOUT = 15 * 60 * 1000;  // 15 minutes
const SESSION_WARNING_THRESHOLD = 13 * 60 * 1000;  // 2 minutes before expiry
const SESSION_CHECK_INTERVAL = 60 * 1000;  // Check every minute
const DRAG_SENSITIVITY_PX = 5;  // Pixels of movement to trigger drag mode
const MS_PER_DAY = 1000 * 60 * 60 * 24;
const TASK_ROW_HEIGHT = 50;
const MIN_GANTT_BAR_WIDTH = 100;
const MIN_GANTT_HEIGHT = 400;

// Use constants in code:
if (timeSinceLastActivity > SESSION_WARNING_THRESHOLD && !sessionWarningShown) {
    sessionWarningShown = true;
    alert('Your session will expire in 2 minutes due to inactivity. Save your work!');
}

sessionCheckInterval = setInterval(() => {
    // ...
}, SESSION_CHECK_INTERVAL);
```

---

### IF-02: Overly Complex Function - renderGantt() Should Be Split

**File:** `index.html:1231-1470`
**Severity:** INFO
**Category:** Code Quality

**Issue:**
The `renderGantt()` function is **240+ lines** and handles:
1. Data validation and empty state
2. Date range calculation
3. SVG setup and margins
4. Scale creation (x and y axes)
5. Weekday/weekend calculation and drawing
6. Grid lines
7. Bar rendering with drag handlers
8. Bar label rendering
9. Task name rendering
10. Dependency arrow rendering
11. Axis rendering

This violates the **Single Responsibility Principle**. The function is difficult to test, understand, and maintain.

**Impact:**
- **Debugging difficulty**: Hard to isolate which part has a bug
- **Testing**: Can't unit test individual components (date logic, scaling, rendering)
- **Reusability**: Can't reuse parts (e.g., scale calculation) in other functions
- **Cognitive load**: Takes time to understand the entire function

**Recommended Fix:**
Split into smaller functions:

```javascript
function renderGantt() {
    const container = document.getElementById('gantt-container');
    container.innerHTML = '';

    if (!currentProjectId) {
        showEmptyState(container, 'Select a project to view Gantt chart');
        return;
    }

    const project = projects.find(p => p.id === currentProjectId);
    if (!project || project.tasks.length === 0) {
        showEmptyState(container, 'No tasks. Add a task to see the Gantt chart.');
        return;
    }

    const ganttData = calculateGanttData(project.tasks);
    const svg = createSvgElement(container, ganttData.width, ganttData.height);
    
    drawWeekendBlocks(svg, ganttData);
    drawGridLines(svg, ganttData);
    drawTaskBars(svg, ganttData);
    drawTaskNames(svg, ganttData);
    drawDependencyArrows(svg, ganttData);
    drawAxes(svg, ganttData);
    
    // Store current state for drag handlers
    updateDragContext(ganttData);
}

function calculateGanttData(tasks) {
    // Extract date range, scale calculations
    const dates = tasks.flatMap(t => [new Date(t.startDate), new Date(t.endDate)]);
    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));
    const totalWeekdays = countWeekdays(minDate, maxDate);
    
    return {
        tasks,
        minDate,
        maxDate,
        totalWeekdays,
        width: /* ... */,
        height: /* ... */,
        margins: /* ... */,
        xScale: /* ... */,
        yScale: /* ... */
    };
}

function drawWeekendBlocks(svg, ganttData) {
    // Extract weekend block logic
}

// ... continue splitting
```

---

### IF-03: No Error Logging for Database Operations

**File:** `server.py:105-109, 161-167`
**Severity:** INFO
**Category:** Quality

**Issue:**
When database initialization fails (lines 105-109), only a generic error message is printed. No details about:
- Which table failed to create
- What SQL error occurred
- Stack trace for debugging

This makes production debugging difficult.

**Current Code:**
```python
except Exception as e:
    print(f"Error initializing SQLite database: {e}")
```

**Impact:**
- **Debugging**: Hard to know what went wrong with database
- **Monitoring**: Can't track which operations fail
- **Support**: Can't help users troubleshoot database issues
- **Reliability**: Silent failures could go unnoticed

**Recommended Fix:**
```python
import traceback

except Exception as e:
    print(f"Error initializing SQLite database: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    # Could also log to a file:
    # with open('error.log', 'a') as f:
    #     f.write(f"{datetime.now()}: {traceback.format_exc()}\n")
```

---

### IF-04: Unused Functions - save_projects() and save_users()

**File:** `server.py:322-325, 354-357`
**Severity:** INFO
**Category:** Code Quality

**Issue:**
The `save_projects()` and `save_users()` functions exist but do nothing:

```python
def save_projects(self, projects):
    """Save projects to database (not used anymore, but kept for compatibility)"""
    pass

def save_users(self, users):
    """Save users to database (not used anymore, but kept for compatibility)"""
    pass
```

These are dead code. They should either be removed or, if needed for backwards compatibility, that should be clearly documented.

**Impact:**
- **Confusion**: Developers might try to use these functions
- **Maintenance**: Unused code makes the codebase harder to understand
- **Technical debt**: Accumulation of dead code degrades code quality

**Recommended Fix:**
Remove if no longer needed:

```python
# Delete save_projects() and save_users() entirely

# If compatibility is needed, add a comment explaining why:
# Note: save_projects() and save_users() methods removed - all data is persisted to
# database in real-time through API handlers. No JSON file backup is needed.
```

---

### IF-05: Inconsistent Error Response Format

**File:** `server.py:400-564`
**Severity:** INFO
**Category:** Quality

**Issue:**
API endpoints return error responses in various formats:
- `{'error': 'message'}` (most common)
- `{'message': 'Logged out successfully'}` (POST /logout)
- `{'success': True}` (DELETE endpoints)
- `{'username': ..., 'token': ..., 'message': ...}` (POST /register)

This inconsistency makes client-side error handling complicated.

**Current Code:**
```python
# Different formats:
self.send_json(401, {'error': 'Not authenticated'})
self.send_json(200, {'message': 'Logged in successfully'})  # Why 'message' here?
self.send_json(200, {'success': True})  # Why 'success'?
```

**Impact:**
- **Client complexity**: Frontend must check for `error`, `message`, or `success`
- **Inconsistency**: Makes API harder to use and understand
- **Bugs**: Easy to miss an error response format
- **Documentation**: API contract is unclear

**Recommended Fix:**
Standardize on a single format:

```python
# Standard success response
{
    "success": true,
    "data": { /* response data */ },
    "message": "Optional human-readable message"
}

# Standard error response
{
    "success": false,
    "error": "Error code",
    "message": "Human-readable error message"
}

# Example:
self.send_json(200, {
    'success': True,
    'data': {'username': username, 'token': token},
    'message': 'Logged in successfully'
})

self.send_json(401, {
    'success': False,
    'error': 'INVALID_CREDENTIALS',
    'message': 'Invalid username or password'
})
```

---

### IF-06: No CORS Preflight Handling for Complex Requests

**File:** `server.py:982-987`
**Severity:** INFO
**Category:** Quality

**Issue:**
The server handles OPTIONS requests (CORS preflight) globally, but doesn't provide specific headers for different endpoints. This could cause issues with:
- Credentials-based requests (withCredentials: true)
- Custom headers like X-CSRF-Token
- Different methods on different endpoints

**Current Code:**
```python
def do_OPTIONS(self):
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    self.end_headers()
```

**Impact:**
- **Limited credential support**: Can't enable withCredentials
- **Missing CSRF support**: X-CSRF-Token header not whitelisted
- **Compatibility**: Some browsers might reject requests with custom headers

**Recommended Fix:**
```python
def do_OPTIONS(self):
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGIN)  # Not '*'
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-CSRF-Token')
    self.send_header('Access-Control-Allow-Credentials', 'true')  # For cookies
    self.send_header('Access-Control-Max-Age', '86400')  # Cache preflight for 24 hours
    self.end_headers()
```

---

### IF-07: Dependency Injection Missing in HTML Rendering

**File:** `index.html:1169-1175`
**Severity:** INFO
**Category:** Code Quality

**Issue:**
The `renderProjectsList()` function directly accesses the global `projects` array and `currentProjectId` variable, making it tightly coupled to global state. This makes testing and reuse difficult.

**Current Code:**
```javascript
function renderProjectsList() {
    const container = document.getElementById('projectsList');
    container.innerHTML = projects.map(project => `
        <div class="project-item ${project.id === currentProjectId ? 'active' : ''}" 
             onclick="selectProject('${project.id}')">
            <div class="project-item-name">${project.name}</div>
            <div class="project-item-count">${project.tasks.length} tasks</div>
        </div>
    `).join('');
}
```

**Impact:**
- **Testing**: Can't test rendering logic in isolation
- **Reusability**: Can't use function with different projects array
- **Refactoring**: Changes to global state require changing multiple functions

**Recommended Fix:**
```javascript
function renderProjectsList(projectsList = projects, activeId = currentProjectId) {
    const container = document.getElementById('projectsList');
    container.innerHTML = projectsList.map(project => `
        <div class="project-item ${project.id === activeId ? 'active' : ''}" 
             data-project-id="${project.id}">
            <div class="project-item-name">${escapeHtml(project.name)}</div>
            <div class="project-item-count">${project.tasks.length} tasks</div>
        </div>
    `).join('');
}
```

---

### IF-08: Console Errors Not Sanitized - Could Leak Sensitive Info

**File:** `index.html:831, 989, 1018, 1149, 1163, 1497`
**Severity:** INFO
**Category:** Security / Quality

**Issue:**
Errors are logged to console with `console.error()`, which in production environments could expose sensitive information:
- Full API URLs with potential parameters
- Internal error messages from server
- Stack traces that reveal application structure

While `console.error` is appropriate for development, in production environments (especially when users' browsers can be inspected), this could leak information.

**Current Code:**
```javascript
catch (error) {
    console.error('Auth check failed:', error);  // Could log API URL, server errors
    showAuthUI();
}

catch (error) {
    console.error('Error loading projects:', error);  // Could reveal server structure
}
```

**Impact:**
- **Information disclosure**: Attackers can inspect browser console to understand API structure
- **Error details leak**: Server error messages could reveal vulnerabilities
- **Stack traces**: Could expose file paths and internal application structure

**Recommended Fix:**
```javascript
catch (error) {
    // In development, log full error
    if (isDevelopment) {
        console.error('Auth check failed:', error);
    } else {
        // In production, log minimal info
        console.error('Authentication failed');
        // Optionally send error to server for monitoring:
        // reportError({ type: 'auth_check', timestamp: Date.now() });
    }
    showAuthUI();
}
```

---

### IF-09: No Input Sanitization for Task Names in UI

**File:** `index.html:1172, 1193, 1414, 1435`
**Severity:** INFO
**Category:** Security

**Issue:**
Task names are rendered directly into HTML without escaping in multiple places:
```javascript
<div class="project-item-name">${project.name}</div>  // Line 1172
<strong>${task.name}</strong>  // Line 1193
return d.name.substring(...);  // Line 1414
```

While the backend stores task names safely, if task names ever contain HTML or JavaScript (even if accidental), it could cause rendering issues or XSS.

**Current Code:**
```javascript
// No escaping of task.name
<strong>${task.name}</strong><br>
```

**Impact:**
- **Potential XSS**: If task names contain `<script>` or `<img onerror=...>`
- **Rendering bugs**: If names contain HTML tags, they might render unexpectedly
- **Display corruption**: Special characters like `<`, `>`, `&` might break layout

**Recommended Fix:**
Implement `escapeHtml()` function (mentioned in CR-01) and use it everywhere:

```javascript
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Use in all rendering:
<strong>${escapeHtml(task.name)}</strong><br>
<div class="project-item-name">${escapeHtml(project.name)}</div>
```

---

### IF-10: No Timeout on API Requests

**File:** `index.html:817, 890, 930, 980, 1003, 1125, 1156, 1474`
**Severity:** INFO
**Category:** Quality

**Issue:**
All `fetch()` calls lack a timeout mechanism. If the server is slow or hung, the browser will wait forever (until browser's internal timeout, typically 30-60 seconds). This creates poor UX:
- User doesn't know if the request is still pending
- No way to manually cancel
- No feedback about what's happening

**Current Code:**
```javascript
const response = await fetch('/api/projects', {
    headers: { 'Authorization': `Bearer ${authToken}` }
});
// No timeout - could hang indefinitely
```

**Impact:**
- **Poor UX**: User interface appears frozen
- **Resource waste**: Browser wastes memory and CPU waiting
- **No feedback**: User doesn't know what's happening
- **Inability to cancel**: Can't abort slow requests

**Recommended Fix:**
```javascript
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout');
        }
        throw error;
    }
}

// Use in API calls:
const response = await fetchWithTimeout('/api/projects', {
    headers: { 'Authorization': `Bearer ${authToken}` }
}, 10000);
```

---

## Summary by File

### index.html
- **Critical:** 3 (XSS vulnerability, race condition, missing date validation)
- **Warning:** 4 (missing error handling, undefined element, unchecked array, missing response check)
- **Info:** 7 (magic numbers, complex functions, unused functions, inconsistent formats, no timeout)

**Total:** 14 issues

### server.py
- **Critical:** 3 (bare except clauses × 2, CORS misconfiguration)
- **Warning:** 4 (unvalidated project input, bare except in normalize_task, missing logging)
- **Info:** 3 (dead code, inconsistent responses, CORS headers)

**Total:** 10 issues

---

## Recommendations (Prioritized)

### 🔴 This Sprint (Critical - MUST FIX)

1. **CR-01: Fix XSS vulnerability** - Replace inline onclick handlers with event delegation
   - Effort: 2-3 hours
   - Risk: High - active user-facing feature
   - Blocks: Cannot deploy with this vulnerability

2. **CR-02: Fix drag-and-drop race condition** - Implement update queue and locking
   - Effort: 3-4 hours
   - Risk: Medium - affects complex drag logic
   - Blocks: Data corruption risk in production

3. **CR-05: Fix CORS and add CSRF protection** - Restrict origin, implement CSRF tokens
   - Effort: 4-5 hours
   - Risk: High - security critical
   - Blocks: Open to cross-site attacks without fix

4. **CR-03, CR-04, CR-06: Fix bare except clauses** - Replace with specific exception handling
   - Effort: 1 hour each
   - Risk: Low - improves error handling
   - Blocks: Prevents silent failures

### 🟡 Next Sprint (Warnings - Should Fix)

5. **WR-02: Fix undefined element reference** - Implement dependencies list or remove code
   - Effort: 1-2 hours
   - Impact: Feature doesn't work currently

6. **WR-01, WR-04: Add proper error feedback** - Display errors to users
   - Effort: 2 hours
   - Impact: UX improvement, better debugging

7. **WR-07: Fix event listener memory leaks** - Implement event delegation
   - Effort: 2-3 hours
   - Impact: Long-term performance and stability

8. **WR-06: Validate project creation input** - Add server-side validation
   - Effort: 1 hour
   - Impact: Data integrity

### 📋 Backlog (Info - Nice to Have)

9. **IF-01, IF-02: Code quality refactoring** - Extract constants, split functions
10. **IF-03 to IF-10: Documentation and consistency improvements**

---

## Testing Notes

**Before deploying Phase 1, recommend testing:**

1. **Security tests:**
   - Try creating task with name: `<img src=x onerror="alert('XSS')">` 
   - Verify task renders as text, not as image
   - Try CSRF attack from different domain (should fail after CR-05 fix)

2. **Race condition tests:**
   - Rapidly drag task left/right, then drop
   - Verify final position matches server state
   - Drag task while waiting for previous drag to complete
   - Verify tasks don't jump or get corrupted

3. **Input validation tests:**
   - Create task with end date before start date
   - Create task with empty date fields
   - Create task with 1MB+ description
   - Verify proper validation messages appear

4. **Error handling tests:**
   - Disconnect from server, try loading projects
   - Verify error message is shown to user
   - Try operations with invalid auth token
   - Verify proper error responses

5. **Memory leak tests:**
   - Open DevTools → Memory tab
   - Switch tabs rapidly 100+ times
   - Take heap snapshot before/after
   - Verify heap size doesn't grow unbounded

6. **Session timeout tests:**
   - Log in, wait 13 minutes → verify warning appears
   - Wait to 15 minutes → verify logout occurs
   - Perform API calls, verify timeout resets

---

**Review completed:** 2026-05-08
**Reviewer:** Code Review Agent (gsd-code-reviewer)
**Depth:** standard
