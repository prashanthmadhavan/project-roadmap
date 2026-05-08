#!/usr/bin/env python3
import json
import os
import hashlib
import secrets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/task_gantt')

class AuthHandler(SimpleHTTPRequestHandler):
    """Handle authentication and project management"""
    
    # Store active sessions: token -> username
    sessions = {}

    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            raise

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id VARCHAR(255) PRIMARY KEY,
                    owner VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (owner) REFERENCES users(username)
                )
            ''')
            
            # Create tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(255) PRIMARY KEY,
                    project_id VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    dependencies TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error initializing database: {e}")
        finally:
            cursor.close()
            conn.close()

    def load_projects(self):
        """Load all projects from database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('SELECT * FROM projects')
            projects = cursor.fetchall()
            
            # Load tasks for each project
            for project in projects:
                cursor.execute('SELECT * FROM tasks WHERE project_id = %s', (project['id'],))
                tasks = cursor.fetchall()
                project['tasks'] = [dict(t) for t in tasks]
                # Convert dependencies from JSON string to list
                for task in project['tasks']:
                    if task.get('dependencies'):
                        task['dependencies'] = json.loads(task['dependencies'])
                    else:
                        task['dependencies'] = []
            
            cursor.close()
            conn.close()
            
            return [dict(p) for p in projects]
        except psycopg2.Error as e:
            print(f"Error loading projects: {e}")
            return []

    def save_projects(self, projects):
        """Save projects to database (not used anymore, but kept for compatibility)"""
        # Projects are saved directly to DB in CRUD operations
        pass

    def load_users(self):
        """Load all users from database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('SELECT username, password, created_at FROM users')
            users = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(u) for u in users]
        except psycopg2.Error as e:
            print(f"Error loading users: {e}")
            return []

    def save_users(self, users):
        """Save users to database (not used anymore, but kept for compatibility)"""
        # Users are saved directly to DB in CRUD operations
        pass

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
                
                # Check if username already exists and create new user in database
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                try:
                    # Try to insert the user
                    hashed_password = self.hash_password(password)
                    cursor.execute(
                        'INSERT INTO users (username, password) VALUES (%s, %s)',
                        (username, hashed_password)
                    )
                    conn.commit()
                    
                    # Create session token
                    token = secrets.token_urlsafe(32)
                    self.sessions[token] = username
                    
                    self.send_json(201, {
                        'username': username,
                        'token': token,
                        'message': 'Account created successfully'
                    })
                except psycopg2.IntegrityError:
                    conn.rollback()
                    self.send_json(400, {'error': 'Username already exists'})
                finally:
                    cursor.close()
                    conn.close()
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
                
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute('SELECT username, password FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                
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
                project_id = str(int(time.time() * 1000))
                
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    'INSERT INTO projects (id, owner, name, description) VALUES (%s, %s, %s, %s)',
                    (project_id, username, data.get('name'), data.get('description', ''))
                )
                conn.commit()
                cursor.close()
                conn.close()
                
                new_project = {
                    'id': project_id,
                    'owner': username,
                    'name': data.get('name'),
                    'description': data.get('description', ''),
                    'created_at': time.strftime('%Y-%m-%d'),
                    'tasks': []
                }
                
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
                
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Verify project exists and belongs to user
                cursor.execute('SELECT owner FROM projects WHERE id = %s', (project_id,))
                project = cursor.fetchone()
                
                if not project or project['owner'] != username:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                task_id = str(int(time.time() * 1000))
                dependencies_json = json.dumps(data.get('dependencies', []))
                
                cursor.execute(
                    'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (%s, %s, %s, %s, %s, %s)',
                    (task_id, project_id, data.get('name'), data.get('startDate'), data.get('endDate'), dependencies_json)
                )
                conn.commit()
                
                new_task = {
                    'id': task_id,
                    'name': data.get('name'),
                    'startDate': data.get('startDate'),
                    'endDate': data.get('endDate'),
                    'dependencies': data.get('dependencies', [])
                }
                
                cursor.close()
                conn.close()
                
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
                
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Verify project exists and belongs to user
                cursor.execute('SELECT * FROM projects WHERE id = %s AND owner = %s', (project_id, username))
                project = cursor.fetchone()
                
                if not project:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                # Update project
                cursor.execute(
                    'UPDATE projects SET name = %s, description = %s WHERE id = %s',
                    (data.get('name', project['name']), data.get('description', project['description']), project_id)
                )
                conn.commit()
                
                # Fetch updated project
                cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
                updated_project = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
                self.send_json(200, dict(updated_project))
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        # PUT /api/projects/<project_id>/tasks/<task_id> - Update task
        elif len(path_parts) >= 6 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            task_id = path_parts[5]
            try:
                data = json.loads(body)
                
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Verify project exists and belongs to user
                cursor.execute('SELECT owner FROM projects WHERE id = %s', (project_id,))
                project = cursor.fetchone()
                
                if not project or project['owner'] != username:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                # Verify task exists
                cursor.execute('SELECT * FROM tasks WHERE id = %s AND project_id = %s', (task_id, project_id))
                task = cursor.fetchone()
                
                if not task:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Task not found'})
                    return
                
                # Update task
                dependencies_json = json.dumps(data.get('dependencies', task['dependencies'] if task['dependencies'] else []))
                cursor.execute(
                    'UPDATE tasks SET name = %s, start_date = %s, end_date = %s, dependencies = %s WHERE id = %s',
                    (data.get('name', task['name']), data.get('startDate', task['start_date']), data.get('endDate', task['end_date']), dependencies_json, task_id)
                )
                conn.commit()
                
                # Fetch updated task
                cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
                updated_task = cursor.fetchone()
                
                updated_task_dict = dict(updated_task)
                # Convert dependencies from JSON string to list
                if updated_task_dict.get('dependencies'):
                    updated_task_dict['dependencies'] = json.loads(updated_task_dict['dependencies'])
                else:
                    updated_task_dict['dependencies'] = []
                
                cursor.close()
                conn.close()
                
                self.send_json(200, updated_task_dict)
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
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Verify project exists and belongs to user
                cursor.execute('SELECT owner FROM projects WHERE id = %s', (project_id,))
                project = cursor.fetchone()
                
                if not project or project[0] != username:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                # Delete project (tasks will be deleted due to CASCADE)
                cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))
                conn.commit()
                cursor.close()
                conn.close()
                
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        # DELETE /api/projects/<project_id>/tasks/<task_id> - Delete task
        elif len(path_parts) >= 6 and path_parts[2] == 'projects' and path_parts[4] == 'tasks':
            project_id = path_parts[3]
            task_id = path_parts[5]
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Verify project exists and belongs to user
                cursor.execute('SELECT owner FROM projects WHERE id = %s', (project_id,))
                project = cursor.fetchone()
                
                if not project or project[0] != username:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Project not found'})
                    return
                
                # Verify task exists
                cursor.execute('SELECT id FROM tasks WHERE id = %s AND project_id = %s', (task_id, project_id))
                task = cursor.fetchone()
                
                if not task:
                    cursor.close()
                    conn.close()
                    self.send_json(404, {'error': 'Task not found'})
                    return
                
                # Delete task
                cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
                conn.commit()
                cursor.close()
                conn.close()
                
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

def init_database():
    """Initialize database schema on startup"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR(255) PRIMARY KEY,
                owner VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (owner) REFERENCES users(username)
            )
        ''')
        
        # Create tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR(255) PRIMARY KEY,
                project_id VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                dependencies TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
    except psycopg2.Error as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Database will be created on first request")
    except Exception as e:
        print(f"Warning: Database initialization error: {e}")

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    server = HTTPServer((host, port), AuthHandler)
    print(f'Server running at http://{host}:{port}')
    print('Press Ctrl+C to stop')
    server.serve_forever()
