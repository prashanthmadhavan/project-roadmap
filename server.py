#!/usr/bin/env python3
import json
import os
import hashlib
import secrets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time

DATA_DIR = '.'
PROJECTS_FILE = os.path.join(DATA_DIR, 'projects.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

class AuthHandler(SimpleHTTPRequestHandler):
    """Handle authentication and project management"""
    
    # Store active sessions: token -> username
    sessions = {}

    def load_projects(self):
        """Load all projects from file"""
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_projects(self, projects):
        """Save all projects to file"""
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)

    def load_users(self):
        """Load all users from file"""
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_users(self, users):
        """Save all users to file"""
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)

    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"

    def verify_password(self, password, hashed):
        """Verify password against hash"""
        try:
            salt, hash_hex = hashed.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hash_hex == hash_obj.hex()
        except:
            return False

    def get_auth_token(self):
        """Extract auth token from headers"""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    def get_current_user(self):
        """Get current authenticated user from token"""
        token = self.get_auth_token()
        if token and token in self.sessions:
            return self.sessions[token]
        return None

    def send_json(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        # GET /api/auth/me - Get current user
        if parsed_path.path == '/api/auth/me':
            username = self.get_current_user()
            if username:
                self.send_json(200, {'username': username})
            else:
                self.send_json(401, {'error': 'Not authenticated'})
        
        # GET /api/projects - Get user's projects
        elif parsed_path.path == '/api/projects':
            username = self.get_current_user()
            if not username:
                self.send_json(401, {'error': 'Not authenticated'})
                return
            
            all_projects = self.load_projects()
            user_projects = [p for p in all_projects if p.get('owner') == username]
            self.send_json(200, user_projects)
        
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
        
        # POST /api/auth/register - Register new user
        if parsed_path.path == '/api/auth/register':
            try:
                data = json.loads(body)
                username = data.get('username', '').strip()
                password = data.get('password', '')
                
                # Validate inputs
                if not username or len(username) < 3:
                    self.send_json(400, {'error': 'Username must be at least 3 characters'})
                    return
                
                if len(password) < 8:
                    self.send_json(400, {'error': 'Password must be at least 8 characters'})
                    return
                
                # Check password has uppercase and lowercase
                if not any(c.isupper() for c in password):
                    self.send_json(400, {'error': 'Password must contain uppercase letters'})
                    return
                
                if not any(c.islower() for c in password):
                    self.send_json(400, {'error': 'Password must contain lowercase letters'})
                    return
                
                # Check if username already exists
                users = self.load_users()
                if any(u['username'] == username for u in users):
                    self.send_json(400, {'error': 'Username already exists'})
                    return
                
                # Create new user
                new_user = {
                    'username': username,
                    'password': self.hash_password(password),
                    'createdAt': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                users.append(new_user)
                self.save_users(users)
                
                # Create session token
                token = secrets.token_urlsafe(32)
                self.sessions[token] = username
                
                self.send_json(201, {
                    'username': username,
                    'token': token,
                    'message': 'Account created successfully'
                })
            except json.JSONDecodeError:
                self.send_json(400, {'error': 'Invalid JSON'})
            except Exception as e:
                self.send_json(500, {'error': str(e)})
        
        # POST /api/auth/login - Login user
        elif parsed_path.path == '/api/auth/login':
            try:
                data = json.loads(body)
                username = data.get('username', '')
                password = data.get('password', '')
                
                users = self.load_users()
                user = next((u for u in users if u['username'] == username), None)
                
                if not user or not self.verify_password(password, user['password']):
                    self.send_json(401, {'error': 'Invalid username or password'})
                    return
                
                # Create session token
                token = secrets.token_urlsafe(32)
                self.sessions[token] = username
                
                self.send_json(200, {
                    'username': username,
                    'token': token,
                    'message': 'Logged in successfully'
                })
            except json.JSONDecodeError:
                self.send_json(400, {'error': 'Invalid JSON'})
            except Exception as e:
                self.send_json(500, {'error': str(e)})
        
        # POST /api/auth/logout - Logout user
        elif parsed_path.path == '/api/auth/logout':
            token = self.get_auth_token()
            if token and token in self.sessions:
                del self.sessions[token]
            self.send_json(200, {'message': 'Logged out successfully'})
        
        # POST /api/projects - Create new project
        elif parsed_path.path == '/api/projects':
            username = self.get_current_user()
            if not username:
                self.send_json(401, {'error': 'Not authenticated'})
                return
            
            try:
                data = json.loads(body)
                projects = self.load_projects()
                
                new_project = {
                    'id': str(int(time.time() * 1000)),
                    'owner': username,
                    'name': data.get('name'),
                    'description': data.get('description', ''),
                    'createdAt': time.strftime('%Y-%m-%d'),
                    'tasks': []
                }
                
                projects.append(new_project)
                self.save_projects(projects)
                
                self.send_json(201, new_project)
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        # POST /api/projects/<project_id>/tasks - Add task to project
        elif len(parsed_path.path.split('/')) >= 5 and '/projects/' in parsed_path.path and '/tasks' in parsed_path.path:
            username = self.get_current_user()
            if not username:
                self.send_json(401, {'error': 'Not authenticated'})
                return
            
            project_id = parsed_path.path.split('/')[3]
            try:
                data = json.loads(body)
                projects = self.load_projects()
                project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)
                
                if not project:
                    self.send_json(404, {'error': 'Project not found'})
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
                
                self.send_json(201, new_task)
            except Exception as e:
                self.send_json(400, {'error': str(e)})

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        username = self.get_current_user()
        if not username:
            self.send_json(401, {'error': 'Not authenticated'})
            return
        
        # PUT /api/projects/<project_id> - Update project
        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'projects' and len(path_parts) == 4:
            project_id = path_parts[3]
            try:
                data = json.loads(body)
                projects = self.load_projects()
                project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)
                
                if not project:
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                project['name'] = data.get('name', project['name'])
                project['description'] = data.get('description', project['description'])
                self.save_projects(projects)
                
                self.send_json(200, project)
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        # PUT /api/projects/<project_id>/tasks/<task_id> - Update task
        elif len(path_parts) >= 6 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            task_id = path_parts[5]
            try:
                data = json.loads(body)
                projects = self.load_projects()
                project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)
                
                if not project:
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                task = next((t for t in project['tasks'] if t['id'] == task_id), None)
                if not task:
                    self.send_json(404, {'error': 'Task not found'})
                    return
                
                task['name'] = data.get('name', task['name'])
                task['startDate'] = data.get('startDate', task['startDate'])
                task['endDate'] = data.get('endDate', task['endDate'])
                task['dependencies'] = data.get('dependencies', task['dependencies'])
                self.save_projects(projects)
                
                self.send_json(200, task)
            except Exception as e:
                self.send_json(400, {'error': str(e)})

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        username = self.get_current_user()
        if not username:
            self.send_json(401, {'error': 'Not authenticated'})
            return
        
        # DELETE /api/projects/<project_id> - Delete project
        if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'projects' and len(path_parts) == 4:
            project_id = path_parts[3]
            try:
                projects = self.load_projects()
                project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)
                
                if not project:
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                projects = [p for p in projects if p['id'] != project_id]
                self.save_projects(projects)
                
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        # DELETE /api/projects/<project_id>/tasks/<task_id> - Delete task
        elif len(path_parts) >= 6 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            task_id = path_parts[5]
            try:
                projects = self.load_projects()
                project = next((p for p in projects if p['id'] == project_id and p['owner'] == username), None)
                
                if not project:
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                project['tasks'] = [t for t in project['tasks'] if t['id'] != task_id]
                self.save_projects(projects)
                
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def translate_path(self, path):
        if path == '/' or path == '':
            path = '/index.html'
        return super().translate_path(path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    server = HTTPServer((host, port), AuthHandler)
    print(f'Server running at http://{host}:{port}')
    print('Press Ctrl+C to stop')
    server.serve_forever()
