# Multi-Project Feature Guide

## Overview

The Task Gantt Chart application now supports **multiple projects** with **project-scoped tasks**. Each project has its own set of tasks, dependencies, and Gantt chart visualization.

---

## New Features

### 1. Project Management
- **Create Projects**: Add new projects with name and description
- **List Projects**: View all projects in the sidebar
- **Select Project**: Click to switch between projects
- **Edit Project**: Update project name and description
- **Delete Project**: Remove entire project and all its tasks

### 2. Project-Scoped Tasks
- Each project has its own task list
- Tasks are only visible when project is selected
- Task dependencies work within the same project
- Task IDs are unique per project

### 3. Improved UI
- **Sidebar**: Project list on the left
- **Tabs**: Switch between "All Projects" and "New Project"
- **Project Info**: Shows project name, description, and task count
- **Context-aware**: Task form appears only when project is selected

### 4. Data Organization
- `projects.json` replaces `tasks.json`
- Each project contains an array of tasks
- Full project metadata stored (name, description, creation date)

---

## User Interface

### Left Sidebar

**Projects Section:**
```
Projects
├── All Projects Tab
│   └── [Project List]
│       └── [Click to select project]
└── + New Tab
    ├── Project Name input
    ├── Description textarea
    └── Create Project button
```

**Tasks Section (appears when project selected):**
```
Tasks
├── Project Info (name, description, task count)
├── Task Form
│   ├── Task Name
│   ├── Start Date
│   ├── End Date
│   ├── Dependencies (dropdown + add button)
│   └── Add Task button
└── Tasks List
    ├── [Task 1]
    │   ├── Dates
    │   ├── Edit button
    │   └── Delete button
    ├── [Task 2]
    └── ...
```

### Main Area

**Project Selection:**
```
Select a project to view tasks and Gantt chart
```

**Project Gantt Chart:**
```
[Project Name] - Gantt Chart
├── Timeline (dates on bottom)
├── Task Bars (colored rectangles)
├── Task Names (left axis)
└── Dependency Arrows (orange lines)
```

---

## API Structure

### Projects API

```
GET /api/projects
Returns all projects with their tasks

POST /api/projects
Create new project
Body: { "name": "...", "description": "..." }

GET /api/projects/<project_id>
Get specific project with all its tasks

PUT /api/projects/<project_id>
Update project metadata
Body: { "name": "...", "description": "..." }

DELETE /api/projects/<project_id>
Delete project and all its tasks
```

### Tasks API (Project-Scoped)

```
POST /api/projects/<project_id>/tasks
Add task to project
Body: { 
  "name": "...", 
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "dependencies": ["task_id_1", "task_id_2"]
}

PUT /api/projects/<project_id>/tasks/<task_id>
Update task in project
Body: { same as POST }

DELETE /api/projects/<project_id>/tasks/<task_id>
Delete task from project
```

---

## Database Schema

### projects.json Structure

```json
[
  {
    "id": "1234567890",
    "name": "Hotel Supply: Connectivity",
    "description": "Q1-Q3 supply chain optimization",
    "createdAt": "2026-01-01",
    "tasks": [
      {
        "id": "1-1",
        "name": "Phase 2 Destinations",
        "startDate": "2026-02-01",
        "endDate": "2026-03-15",
        "dependencies": []
      },
      {
        "id": "1-2",
        "name": "Phase 3 Destinations",
        "startDate": "2026-03-01",
        "endDate": "2026-03-23",
        "dependencies": ["1-1"]
      }
    ]
  }
]
```

### Key Design Decisions

- **Nested Structure**: Tasks live within projects
- **Scoped IDs**: Task IDs are unique within projects (e.g., "1-1", "1-2")
- **Metadata**: Projects include creation date and description
- **Dependencies**: Tasks reference other tasks in the same project

---

## Test Data

### 6 Sample Projects (35 Tasks Total)

1. **Hotel Supply: Connectivity & Local Contracts** (5 tasks)
   - Phase 2-5 destination enabling
   - Local contracts go live

2. **Tech/Platform Work** (5 tasks)
   - Splunk dashboards
   - Monitoring and alerting
   - Automated regression testing
   - TravelGate integration

3. **Automate Product Setup** (6 tasks)
   - Agresso setup
   - Transfers, Cars, Content
   - Product setup optimization

4. **Pricing Rules** (8 tasks)
   - API feeds
   - Price comparison rules
   - Minimum margin protection
   - Bundle pricing

5. **Training & Operations** (6 tasks)
   - Training for various teams
   - Operations support

6. **Hotel Content Model** (5 tasks)
   - Content loading
   - Smart contracts
   - Tritium IDs
   - Data migration

---

## Usage Walkthrough

### Create a New Project

1. Click "Projects" in sidebar
2. Click "+ New" tab
3. Enter "Project Name"
4. (Optional) Enter "Description"
5. Click "Create Project"
6. Project appears in the list

### Add a Task to Project

1. Click a project to select it
2. Tasks section appears on the right
3. Enter task details:
   - **Task Name**: What the task is called
   - **Start Date**: When it starts
   - **End Date**: When it ends
4. (Optional) Add dependencies:
   - Select a task from dropdown
   - Click "Add Dependency"
   - Repeat for multiple dependencies
5. Click "Add Task"
6. Task appears in list and Gantt chart

### View Project Gantt Chart

1. Select a project
2. Gantt chart appears in main area
3. **Green bars** = tasks
4. **Orange arrows** = dependencies
5. **Left axis** = task names
6. **Bottom axis** = dates/timeline

### Edit a Task

1. In tasks list, click "Edit" button
2. Update details in modal
3. Click "Save"
4. Changes apply immediately

### Delete a Task or Project

1. Click "Delete" button
2. Confirm deletion
3. Item is removed

---

## Benefits of Multi-Project

1. **Organization**: Separate different initiatives
2. **Focus**: View one project at a time
3. **Scalability**: Add unlimited projects
4. **Isolation**: Project dependencies don't interfere
5. **Reusability**: Similar tasks across projects
6. **Team Collaboration**: Assign projects to teams

---

## Migration from Old Version

If you have old `tasks.json`:

1. Open `tasks.json`
2. Create a new project structure:
   ```json
   [{
     "id": "1",
     "name": "My Project",
     "description": "Migrated from single-project version",
     "createdAt": "2026-01-01",
     "tasks": [... all your old tasks ...]
   }]
   ```
3. Save as `projects.json`
4. Restart the application

---

## Technical Details

### File Changes

- **server.py**: Updated with project endpoints
- **index.html**: Refactored UI for multi-project
- **projects.json**: New database format (replaces tasks.json)
- **generate_projects_data.py**: Generate test data

### Backwards Compatibility

⚠️ **Breaking Change**: The old `tasks.json` format is not compatible.

If you have existing tasks:
1. Wrap them in a project structure
2. Or regenerate using `generate_projects_data.py`

---

## Future Enhancements

- [ ] Project templates
- [ ] Project sharing/permissions
- [ ] Project archiving
- [ ] Project export/import
- [ ] Milestone support within projects
- [ ] Cross-project timeline view
- [ ] Project comparison
- [ ] Team assignments per project

---

## Troubleshooting

### "No projects found"
- Create a new project using the "+ New" tab
- Or ensure projects.json has valid data

### "Task not appearing in Gantt"
- Verify project is selected (left sidebar)
- Check start and end dates are valid
- Ensure task has a date range

### "Dependencies not showing"
- Dependencies must reference tasks in the same project
- Task IDs are case-sensitive
- Check task IDs match exactly

### "Projects not loading"
- Check projects.json file exists
- Verify JSON format is valid
- Check file permissions
- See server logs for errors

---

## API Examples

### Create a Project (curl)

```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Project description"
  }'
```

### Add a Task (curl)

```bash
curl -X POST http://localhost:5000/api/projects/1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Task Name",
    "startDate": "2026-05-01",
    "endDate": "2026-05-31",
    "dependencies": []
  }'
```

### Update a Task (curl)

```bash
curl -X PUT http://localhost:5000/api/projects/1/tasks/1-1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Task",
    "startDate": "2026-05-05",
    "endDate": "2026-05-25",
    "dependencies": ["1-2"]
  }'
```

---

## Support & Documentation

- **README.md** - Main project documentation
- **HOSTING.md** - Deployment options
- **RENDER_DEPLOYMENT.md** - Render.com specific guide
- **This file** - Multi-project feature guide

---

**Version**: 2.0 (Multi-Project Release)
**Last Updated**: May 2026
