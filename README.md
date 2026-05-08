# Project Roadmap - Task Gantt Chart

An interactive web-based task management application with Gantt chart visualization and dependency tracking.

**🌐 Live Demo**: https://prashanthmadhavan.github.io/project-roadmap/  
**📦 GitHub Repo**: https://github.com/prashanthmadhavan/project-roadmap

## Features

- **Task Management**: Create, read, update, and delete tasks with ease
- **Gantt Chart Visualization**: View all tasks on an interactive timeline
- **Dependency Tracking**: Define task dependencies and visualize them with arrows
- **Real-time Updates**: All changes are immediately reflected in the chart
- **Responsive Design**: Works on desktop and tablet devices
- **Data Persistence**: Tasks are saved to JSON file storage

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

### Adding a Task

1. Enter the task name in the "Task Name" field
2. Select a start date and end date
3. Optionally, select dependent tasks from the "Dependencies" dropdown
4. Click "Add Task" to save

### Managing Dependencies

1. From the task form, select a task from the "Dependencies" dropdown
2. Click "Add Dependency" to add it
3. To remove a dependency, click the "Remove" button next to it

### Editing Tasks

1. Click the "Edit" button on any task in the task list
2. Modify the task details in the modal
3. Click "Save" to apply changes

### Deleting Tasks

1. Click the "Delete" button on any task in the task list
2. Confirm the deletion in the prompt

## Project Structure

```
project-roadmap/
├── server.py                    # Python HTTP server with API endpoints
├── index.html                   # Main application UI
├── tasks.json                   # Task data storage
├── roadmap_test_data.xlsx       # Test data in Excel format
├── generate_test_data.py        # Script to generate test data
├── README.md                    # This file
└── .gitignore                   # Git ignore rules
```

## API Endpoints

The application exposes the following REST API endpoints:

- `GET /api/tasks` - Retrieve all tasks
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/<task_id>` - Update a task
- `DELETE /api/tasks/<task_id>` - Delete a task

### Request/Response Format

**Create Task (POST /api/tasks)**
```json
{
  "name": "Task Name",
  "startDate": "2026-05-01",
  "endDate": "2026-05-31",
  "dependencies": ["task_id_1", "task_id_2"]
}
```

**Task Response**
```json
{
  "id": "1715159234000",
  "name": "Task Name",
  "startDate": "2026-05-01",
  "endDate": "2026-05-31",
  "dependencies": ["task_id_1", "task_id_2"]
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
