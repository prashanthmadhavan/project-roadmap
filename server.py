#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

DATA_FILE = 'projects.json'

class ProjectTaskHandler(SimpleHTTPRequestHandler):
    def load_projects(self):
        """Load all projects from file"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_projects(self, projects):
        """Save all projects to file"""
        with open(DATA_FILE, 'w') as f:
            json.dump(projects, f, indent=2)

    def find_project(self, project_id, projects):
        """Find a project by ID"""
        for project in projects:
            if project['id'] == project_id:
                return project
        return None

    def find_task(self, task_id, tasks):
        """Find a task in a task list"""
        for task in tasks:
            if task['id'] == task_id:
                return task
        return None

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        # GET /api/projects - Get all projects
        if parsed_path.path == '/api/projects':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            projects = self.load_projects()
            self.wfile.write(json.dumps(projects).encode())
        
        # GET /api/projects/<project_id> - Get single project
        elif len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'projects':
            project_id = path_parts[3]
            projects = self.load_projects()
            project = self.find_project(project_id, projects)
            
            if project:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(project).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
        
        # Serve static files
        elif self.path == '/' or self.path == '':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        # POST /api/projects - Create new project
        if parsed_path.path == '/api/projects':
            try:
                data = json.loads(body)
                projects = self.load_projects()
                
                new_project = {
                    'id': str(int(time.time() * 1000)),
                    'name': data.get('name'),
                    'description': data.get('description', ''),
                    'createdAt': time.strftime('%Y-%m-%d'),
                    'tasks': []
                }
                
                projects.append(new_project)
                self.save_projects(projects)
                
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(new_project).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        # POST /api/projects/<project_id>/tasks - Add task to project
        elif len(path_parts) >= 5 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            try:
                data = json.loads(body)
                projects = self.load_projects()
                project = self.find_project(project_id, projects)
                
                if not project:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
                    return
                
                new_task = {
                    'id': str(int(time.time() * 1000)),
                    'name': data.get('name'),
                    'startDate': data.get('startDate'),
                    'endDate': data.get('endDate'),
                    'dependencies': data.get('dependencies', [])
                }
                
                project['tasks'].append(new_task)
                self.save_projects(projects)
                
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(new_task).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        # PUT /api/projects/<project_id> - Update project
        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'projects' and len(path_parts) == 4:
            project_id = path_parts[3]
            try:
                data = json.loads(body)
                projects = self.load_projects()
                project = self.find_project(project_id, projects)
                
                if not project:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
                    return
                
                project['name'] = data.get('name', project['name'])
                project['description'] = data.get('description', project['description'])
                self.save_projects(projects)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(project).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        # PUT /api/projects/<project_id>/tasks/<task_id> - Update task
        elif len(path_parts) >= 6 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            task_id = path_parts[5]
            try:
                data = json.loads(body)
                projects = self.load_projects()
                project = self.find_project(project_id, projects)
                
                if not project:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
                    return
                
                task = self.find_task(task_id, project['tasks'])
                if not task:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Task not found'}).encode())
                    return
                
                task['name'] = data.get('name', task['name'])
                task['startDate'] = data.get('startDate', task['startDate'])
                task['endDate'] = data.get('endDate', task['endDate'])
                task['dependencies'] = data.get('dependencies', task['dependencies'])
                self.save_projects(projects)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(task).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        # DELETE /api/projects/<project_id> - Delete project
        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'projects' and len(path_parts) == 4:
            project_id = path_parts[3]
            try:
                projects = self.load_projects()
                projects = [p for p in projects if p['id'] != project_id]
                self.save_projects(projects)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        # DELETE /api/projects/<project_id>/tasks/<task_id> - Delete task
        elif len(path_parts) >= 6 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            task_id = path_parts[5]
            try:
                projects = self.load_projects()
                project = self.find_project(project_id, projects)
                
                if not project:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Project not found'}).encode())
                    return
                
                project['tasks'] = [t for t in project['tasks'] if t['id'] != task_id]
                self.save_projects(projects)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def translate_path(self, path):
        if path == '/' or path == '':
            path = '/index.html'
        return super().translate_path(path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    server = HTTPServer((host, port), ProjectTaskHandler)
    print(f'Server running at http://{host}:{port}')
    print('Press Ctrl+C to stop')
    server.serve_forever()
