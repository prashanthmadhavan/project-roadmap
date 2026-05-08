# Project Roadmap - Task Gantt Chart

An interactive web-based task management application with Gantt chart visualization and dependency tracking.

**🌐 Live Demo**: https://prashanthmadhavan.github.io/project-roadmap/  
**📦 GitHub Repo**: https://github.com/prashanthmadhavan/project-roadmap

## Features

- **Multi-Project Support**: Create and manage multiple projects independently
- **Project-Scoped Tasks**: Each project has its own tasks and dependencies
- **Task Management**: Create, read, update, and delete tasks with ease
- **Gantt Chart Visualization**: View all tasks on an interactive timeline per project
- **Dependency Tracking**: Define task dependencies and visualize them with arrows
- **Real-time Updates**: All changes are immediately reflected in the chart
- **Responsive Design**: Works on desktop and tablet devices
- **Data Persistence**: Projects and tasks are saved to JSON file storage

## Technologies

- **Backend**: Python 3 (HTTP Server)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Visualization**: D3.js v7
- **Data Format**: JSON

## Quick Start

### Online (No Installation)
Visit: https://prashanthmadhavan.github.io/project-roadmap/
- **Note**: Static view only (can view tasks, but cannot add new ones)
- For full functionality, follow the deployment guide below

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/prashanthmadhavan/project-roadmap.git
cd project-roadmap
```

2. Start the server:
```bash
python3 server.py
```

3. Open your browser:
```
http://127.0.0.1:5000
```

### Deploy Online (With Full Functionality)

**Quick Deployment Options**:
- **Render.com**: https://render.com (recommended)
- **Railway.app**: https://railway.app
- **Replit**: https://replit.com

See [HOSTING.md](HOSTING.md) for detailed deployment instructions for each platform.

## Usage

### Creating a Project

1. Click the **"+ New"** tab in the Projects section
2. Enter the project name and optional description
3. Click **"Create Project"**
4. Your project appears in the projects list

### Adding a Task to Project

1. **Select a project** from the list in the sidebar
2. The task form appears on the right sidebar
3. Enter task details:
   - **Task Name**: Name of the task
   - **Start Date**: When the task starts
   - **End Date**: When the task ends
4. **(Optional)** Add dependencies:
   - Select a task from the dropdown
   - Click "Add Dependency"
5. Click **"Add Task"** to save

### Managing Dependencies

1. From the task form, select a task from the "Dependencies" dropdown
2. Click "Add Dependency" to add it
3. To remove a dependency, click the "Remove" button next to it
4. Dependencies are shown as orange arrows in the Gantt chart

### Viewing Project Gantt Chart

1. Select a project from the sidebar
2. The Gantt chart appears in the main area
3. **Green bars** = tasks with their durations
4. **Orange arrows** = task dependencies
5. Tasks are organized by date timeline

### Editing Tasks

1. Click the **"Edit"** button on any task in the task list
2. Modify the task details in the modal
3. Click **"Save"** to apply changes

### Editing Projects

1. Click the project name in the sidebar
2. Click **"Edit"** icon (appears on hover)
3. Update project name and description
4. Click **"Save"** to apply changes

### Deleting Tasks or Projects

1. Click the **"Delete"** button on the task or project
2. Confirm the deletion in the prompt

## Project Structure

```
project-roadmap/
├── server.py                    # Python HTTP server with API endpoints
├── index.html                   # Main application UI (multi-project)
├── projects.json                # Projects and tasks data storage
├── roadmap_test_data.xlsx       # Legacy test data in Excel format
├── generate_test_data.py        # Legacy test data generator
├── generate_projects_data.py    # Multi-project test data generator
├── README.md                    # This file
├── MULTI_PROJECT_GUIDE.md       # Multi-project feature documentation
├── HOSTING.md                   # Deployment options guide
└── .gitignore                   # Git ignore rules
```

## API Endpoints

The application exposes the following REST API endpoints:

### Projects API

- `GET /api/projects` - Retrieve all projects with their tasks
- `POST /api/projects` - Create a new project
- `PUT /api/projects/<project_id>` - Update a project
- `DELETE /api/projects/<project_id>` - Delete a project and all its tasks

### Tasks API (Project-Scoped)

- `POST /api/projects/<project_id>/tasks` - Add task to a project
- `PUT /api/projects/<project_id>/tasks/<task_id>` - Update a task
- `DELETE /api/projects/<project_id>/tasks/<task_id>` - Delete a task

### Request/Response Format

**Create Project (POST /api/projects)**
```json
{
  "name": "Project Name",
  "description": "Project description"
}
```

**Create Task (POST /api/projects/<project_id>/tasks)**
```json
{
  "name": "Task Name",
  "startDate": "2026-05-01",
  "endDate": "2026-05-31",
  "dependencies": ["task_id_1", "task_id_2"]
}
```

**Project Response**
```json
{
  "id": "1715159234000",
  "name": "Project Name",
  "description": "Project description",
  "createdAt": "2026-05-01",
  "tasks": [
    {
      "id": "1-1",
      "name": "Task Name",
      "startDate": "2026-05-01",
      "endDate": "2026-05-31",
      "dependencies": []
    }
  ]
}
```

## Test Data

The repository includes pre-loaded test data from a real project roadmap (52 tasks with dependencies). Run:

```bash
python3 generate_test_data.py
```

This will create/update:
- `tasks.json` - JSON format for the application
- `roadmap_test_data.xlsx` - Excel format for reference

## Color Legend

- **Green**: Completed tasks or active tasks
- **Yellow**: Work in progress
- **Grey**: Not started
- **Red**: Blockers or flags
- **Orange**: Dependency arrows

## Future Enhancements

- [ ] User authentication and multi-user support
- [ ] Task filtering and search
- [ ] Custom color coding by project/team
- [ ] Export to PDF or image
- [ ] Milestone tracking
- [ ] Resource allocation
- [ ] Integration with project management tools

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please open an issue on GitHub or contact the project maintainer.

---

**Created**: May 2026
**Author**: Prashanth Madhavan
