#!/usr/bin/env python3
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

DATA_FILE = 'tasks.json'

class TaskHandler(SimpleHTTPRequestHandler):
    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_tasks(self, tasks):
        with open(DATA_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/tasks':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            tasks = self.load_tasks()
            self.wfile.write(json.dumps(tasks).encode())
        else:
            # Serve static files
            if self.path == '/' or self.path == '':
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/tasks':
            try:
                data = json.loads(body)
                tasks = self.load_tasks()
                
                task = {
                    'id': str(int(time.time() * 1000)),
                    'name': data.get('name'),
                    'startDate': data.get('startDate'),
                    'endDate': data.get('endDate'),
                    'dependencies': data.get('dependencies', [])
                }
                
                tasks.append(task)
                self.save_tasks(tasks)
                
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(task).encode())
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
        
        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'tasks':
            task_id = path_parts[3]
            try:
                data = json.loads(body)
                tasks = self.load_tasks()
                
                for task in tasks:
                    if task['id'] == task_id:
                        task['name'] = data.get('name', task['name'])
                        task['startDate'] = data.get('startDate', task['startDate'])
                        task['endDate'] = data.get('endDate', task['endDate'])
                        task['dependencies'] = data.get('dependencies', task['dependencies'])
                        self.save_tasks(tasks)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps(task).encode())
                        return
                
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Task not found'}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'tasks':
            task_id = path_parts[3]
            try:
                tasks = self.load_tasks()
                tasks = [t for t in tasks if t['id'] != task_id]
                self.save_tasks(tasks)
                
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
        # Serve files from the current directory
        if path == '/' or path == '':
            path = '/index.html'
        return super().translate_path(path)

if __name__ == '__main__':
    os.chdir('/var/folders/0j/727fsw6n7b72vdhgshwp50tr0000gn/T/opencode/task-gantt')
    server = HTTPServer(('127.0.0.1', 5000), TaskHandler)
    print('Server running at http://127.0.0.1:5000')
    print('Press Ctrl+C to stop')
    server.serve_forever()
