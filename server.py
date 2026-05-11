#!/usr/bin/env python3
import json
import os
import hashlib
import secrets
import sqlite3
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

# Try PostgreSQL first, fall back to SQLite for local development
DATABASE_URL = os.environ.get('DATABASE_URL', None)
USE_POSTGRES = DATABASE_URL is not None
DB_FILE = 'task_gantt.db'
USERS_CONFIG_FILE = 'USERS_CONFIG.json'

if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        print("✓ PostgreSQL mode enabled (DATABASE_URL set)")
    except ImportError:
        print("✗ psycopg2 not available, falling back to SQLite")
        USE_POSTGRES = False
else:
    print(f"⚠ DATABASE_URL not set - using SQLite: {DB_FILE}")
    print("  Note: SQLite data may not persist on Render. Use PostgreSQL for reliable storage.")

# Session timeout in seconds (15 minutes)
SESSION_TIMEOUT = 15 * 60

# Allowed origins for CORS (whitelist specific origins, not wildcard)
ALLOWED_ORIGINS = [
    'http://localhost:5000',
    'http://localhost:8000',
    'http://localhost:8888',
    'http://127.0.0.1:5000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8888',
    'https://project-roadmap.onrender.com',
    os.environ.get('ALLOWED_ORIGIN', ''),  # Allow override via environment variable
]
# Filter out empty strings
ALLOWED_ORIGINS = [origin for origin in ALLOWED_ORIGINS if origin]

class AuthHandler(SimpleHTTPRequestHandler):
    """Handle authentication and project management"""
    
    # Store active sessions: token -> (username, timestamp)
    sessions = {}

    def get_db_connection(self):
        """Get database connection (SQLite or PostgreSQL)"""
        if USE_POSTGRES:
            try:
                conn = psycopg2.connect(DATABASE_URL)
                return conn
            except psycopg2.Error as e:
                print(f"PostgreSQL connection error: {e}")
                raise
        else:
            return sqlite3.connect(DB_FILE)

    def init_db(self):
        """Initialize database schema"""
        if USE_POSTGRES:
            self._init_postgres_db()
        else:
            self._init_sqlite_db()

    def _init_sqlite_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    advanced_mode INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (owner) REFERENCES users(username)
                )
            ''')
            
            # Create tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    dependencies TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            
            # Create demo user if it doesn't exist
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('demo',))
            if cursor.fetchone()[0] == 0:
                self._create_demo_user_sqlite(cursor, conn)
            
        except Exception as e:
            print(f"Error initializing SQLite database: {e}")
        finally:
            cursor.close()
            conn.close()

    def _init_postgres_db(self):
        """Initialize PostgreSQL database"""
        conn = None
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    advanced_mode BOOLEAN DEFAULT FALSE,
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
            
            # Create demo user if it doesn't exist
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', ('demo',))
            if cursor.fetchone()[0] == 0:
                self._create_demo_user_postgres(cursor, conn)
            
            cursor.close()
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error initializing PostgreSQL database: {e}")
        finally:
            if conn:
                conn.close()

    def _create_demo_user_sqlite(self, cursor, conn):
        """Create demo user with test data in SQLite"""
        try:
            # Create demo user
            demo_password = self.hash_password('Demo@1234')
            cursor.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                ('demo', demo_password)
            )
            
            # Create demo project
            project_id = str(int(time.time() * 1000))
            today = datetime.now().date()
            cursor.execute(
                'INSERT INTO projects (id, owner, name, description) VALUES (?, ?, ?, ?)',
                (project_id, 'demo', 'Sample Project', 'This is a demo project to show how the app works')
            )
            
            # Create sample tasks
            tasks = [
                ('Design mockups', today, today + timedelta(days=3)),
                ('Develop backend API', today + timedelta(days=2), today + timedelta(days=7)),
                ('Build frontend UI', today + timedelta(days=3), today + timedelta(days=10)),
                ('Integration testing', today + timedelta(days=8), today + timedelta(days=12)),
                ('Deploy to production', today + timedelta(days=11), today + timedelta(days=13)),
            ]
            
            for idx, (name, start, end) in enumerate(tasks):
                task_id = str(int(time.time() * 1000) + idx)
                cursor.execute(
                    'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (?, ?, ?, ?, ?, ?)',
                    (task_id, project_id, name, start, end, '[]')
                )
            
            conn.commit()
            print("Demo user created with test data")
        except Exception as e:
            print(f"Error creating demo user: {e}")

    def _create_demo_user_postgres(self, cursor, conn):
        """Create demo user with test data in PostgreSQL"""
        try:
            # Create demo user
            demo_password = self.hash_password('Demo@1234')
            cursor.execute(
                'INSERT INTO users (username, password) VALUES (%s, %s)',
                ('demo', demo_password)
            )
            
            # Create demo project
            project_id = str(int(time.time() * 1000))
            today = datetime.now().date()
            cursor.execute(
                'INSERT INTO projects (id, owner, name, description) VALUES (%s, %s, %s, %s)',
                (project_id, 'demo', 'Sample Project', 'This is a demo project to show how the app works')
            )
            
            # Create sample tasks
            tasks = [
                ('Design mockups', today, today + timedelta(days=3)),
                ('Develop backend API', today + timedelta(days=2), today + timedelta(days=7)),
                ('Build frontend UI', today + timedelta(days=3), today + timedelta(days=10)),
                ('Integration testing', today + timedelta(days=8), today + timedelta(days=12)),
                ('Deploy to production', today + timedelta(days=11), today + timedelta(days=13)),
            ]
            
            for idx, (name, start, end) in enumerate(tasks):
                task_id = str(int(time.time() * 1000) + idx)
                cursor.execute(
                    'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (%s, %s, %s, %s, %s, %s)',
                    (task_id, project_id, name, start, end, '[]')
                )
            
            conn.commit()
            print("Demo user created with test data")
        except Exception as e:
            print(f"Error creating demo user: {e}")

    def is_session_valid(self, token):
        """Check if session token is valid and not expired"""
        if token not in self.sessions:
            return False
        
        username, timestamp = self.sessions[token]
        # Check if session has expired (15 minutes)
        if time.time() - timestamp > SESSION_TIMEOUT:
            del self.sessions[token]
            return False
        
        # Refresh timestamp on each access
        self.sessions[token] = (username, time.time())
        return True

    def normalize_task(self, task):
        """Convert snake_case database fields to camelCase for API response"""
        normalized = {
            'id': task.get('id'),
            'projectId': task.get('project_id'),
            'name': task.get('name'),
            'startDate': task.get('start_date'),
            'endDate': task.get('end_date'),
            'dependencies': task.get('dependencies', [])
        }
        # Parse dependencies if it's a JSON string
        if isinstance(normalized['dependencies'], str):
            try:
                normalized['dependencies'] = json.loads(normalized['dependencies'])
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse dependencies for task {task.get('id')}: {e}")
                normalized['dependencies'] = []
            except Exception as e:
                print(f"Unexpected error parsing dependencies: {e}")
                raise
        return normalized

    def load_projects(self):
        """Load all projects from database"""
        try:
            if USE_POSTGRES:
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute('SELECT * FROM projects')
                projects = cursor.fetchall()
                
                # Load tasks for each project
                for project in projects:
                    cursor.execute('SELECT * FROM tasks WHERE project_id = %s', (project['id'],))
                    tasks = cursor.fetchall()
                    # Normalize task fields to camelCase
                    project['tasks'] = [self.normalize_task(dict(t)) for t in tasks]
                
                cursor.close()
                conn.close()
                
                return [dict(p) for p in projects]
            else:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM projects')
                projects = [dict(p) for p in cursor.fetchall()]
                
                # Load tasks for each project
                for project in projects:
                    cursor.execute('SELECT * FROM tasks WHERE project_id = ?', (project['id'],))
                    tasks = [dict(t) for t in cursor.fetchall()]
                    # Normalize task fields to camelCase
                    project['tasks'] = [self.normalize_task(t) for t in tasks]
                
                conn.close()
                return projects
        except Exception as e:
            print(f"Error loading projects: {e}")
            return []

    def save_projects(self, projects):
        """Save projects to database (not used anymore, but kept for compatibility)"""
        pass

    def load_users(self):
        """Load all users from database"""
        try:
            if USE_POSTGRES:
                conn = self.get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute('SELECT username, password, created_at FROM users')
                users = cursor.fetchall()
                
                cursor.close()
                conn.close()
                
                return [dict(u) for u in users]
            else:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT username, password, created_at FROM users')
                users = [dict(u) for u in cursor.fetchall()]
                
                conn.close()
                return users
        except Exception as e:
            print(f"Error loading users: {e}")
            return []

    def save_users(self, users):
        """Save users to database (not used anymore, but kept for compatibility)"""
        pass

    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"

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
            raise

    def get_auth_token(self):
        """Extract auth token from headers"""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    def get_current_user(self):
        """Get current authenticated user from token"""
        token = self.get_auth_token()
        if token and self.is_session_valid(token):
            return self.sessions[token][0]
        return None
     
    def get_user_advanced_mode(self, username):
        """Get user's advanced_mode setting from database"""
        try:
            if USE_POSTGRES:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT advanced_mode FROM users WHERE username = %s', (username,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                return result[0] if result else False
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('SELECT advanced_mode FROM users WHERE username = ?', (username,))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                return bool(result[0]) if result else False
        except Exception:
            return False
     
    def set_user_advanced_mode(self, username, advanced_mode):
        """Set user's advanced_mode setting"""
        try:
            if USE_POSTGRES:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET advanced_mode = %s WHERE username = %s', 
                                (advanced_mode, username))
                conn.commit()
                cursor.close()
                conn.close()
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET advanced_mode = ? WHERE username = ?',
                                (1 if advanced_mode else 0, username))
                conn.commit()
                cursor.close()
                conn.close()
            return True
        except Exception:
            return False

    def send_json(self, status_code, data):
        """Send JSON response with CORS headers restricted to allowed origins"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
         
        # Only allow CORS for whitelisted origins, not wildcard
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
         
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        # GET /api/auth/me - Get current user with advanced_mode flag
        if parsed_path.path == '/api/auth/me':
            username = self.get_current_user()
            if username:
                advanced_mode = self.get_user_advanced_mode(username)
                self.send_json(200, {'username': username, 'advanced_mode': advanced_mode})
            else:
                self.send_json(401, {'error': 'Not authenticated'})
        
        # GET /api/projects - Get all projects (public access)
        elif parsed_path.path == '/api/projects':
            all_projects = self.load_projects()
            self.send_json(200, all_projects)
        
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
                
                # Try to insert the user
                hashed_password = self.hash_password(password)
                
                if USE_POSTGRES:
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute(
                            'INSERT INTO users (username, password) VALUES (%s, %s)',
                            (username, hashed_password)
                        )
                        conn.commit()
                        
                        # Create session token
                        token = secrets.token_urlsafe(32)
                        self.sessions[token] = (username, time.time())
                        
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
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute(
                            'INSERT INTO users (username, password) VALUES (?, ?)',
                            (username, hashed_password)
                        )
                        conn.commit()
                        
                        # Create session token
                        token = secrets.token_urlsafe(32)
                        self.sessions[token] = (username, time.time())
                        
                        self.send_json(201, {
                            'username': username,
                            'token': token,
                            'message': 'Account created successfully'
                        })
                    except sqlite3.IntegrityError:
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
                
                if USE_POSTGRES:
                    conn = self.get_db_connection()
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    
                    cursor.execute('SELECT username, password FROM users WHERE username = %s', (username,))
                    user = cursor.fetchone()
                    cursor.close()
                    conn.close()
                else:
                    conn = sqlite3.connect(DB_FILE)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT username, password FROM users WHERE username = ?', (username,))
                    user = cursor.fetchone()
                    conn.close()
                
                if not user or not self.verify_password(password, user['password']):
                    self.send_json(401, {'error': 'Invalid username or password'})
                    return
                
                # Create session token
                token = secrets.token_urlsafe(32)
                self.sessions[token] = (username, time.time())
                
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
         
        # POST /api/auth/toggle-advanced - Toggle advanced mode
        elif parsed_path.path == '/api/auth/toggle-advanced':
            username = self.get_current_user()
            if not username:
                self.send_json(401, {'error': 'Not authenticated'})
                return
             
            try:
                data = json.loads(body)
                advanced_mode = data.get('advanced_mode', None)
                 
                if advanced_mode is None:
                    self.send_json(400, {'error': 'advanced_mode field is required'})
                    return
                 
                success = self.set_user_advanced_mode(username, advanced_mode)
                if success:
                    self.send_json(200, {'message': 'Advanced mode updated', 'advanced_mode': advanced_mode})
                else:
                    self.send_json(500, {'error': 'Failed to update advanced mode'})
            except json.JSONDecodeError:
                self.send_json(400, {'error': 'Invalid JSON'})
         
        # POST /api/projects - Create new project
        elif parsed_path.path == '/api/projects':
            username = self.get_current_user()
            if not username:
                self.send_json(401, {'error': 'Not authenticated'})
                return
            
            try:
                data = json.loads(body)
                
                # Validate project input
                name = data.get('name', '').strip()
                description = data.get('description', '').strip()
                
                if not name:
                    self.send_json(400, {'error': 'Project name is required'})
                    return
                
                if len(name) > 255:
                    self.send_json(400, {'error': 'Project name is too long (max 255 characters)'})
                    return
                
                if len(description) > 1000:
                    self.send_json(400, {'error': 'Description is too long (max 1000 characters)'})
                    return
                
                project_id = str(int(time.time() * 1000))
                
                if USE_POSTGRES:
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        'INSERT INTO projects (id, owner, name, description) VALUES (%s, %s, %s, %s)',
                        (project_id, username, name, description)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        'INSERT INTO projects (id, owner, name, description) VALUES (?, ?, ?, ?)',
                        (project_id, username, name, description)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                
                new_project = {
                    'id': project_id,
                    'owner': username,
                    'name': name,
                    'description': description,
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
                
                if USE_POSTGRES:
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
                    
                    # Check for duplicate task name (Defect #9)
                    task_name = data.get('name', '').strip()
                    if task_name:
                        cursor.execute('SELECT COUNT(*) FROM tasks WHERE project_id = %s AND LOWER(name) = LOWER(%s)', 
                                      (project_id, task_name))
                        if cursor.fetchone()[0] > 0:
                            cursor.close()
                            conn.close()
                            self.send_json(400, {'error': f'Task name "{task_name}" already exists in this project'})
                            return
                    
                    task_id = str(int(time.time() * 1000))
                    dependencies_json = json.dumps(data.get('dependencies', []))
                    
                    cursor.execute(
                        'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (%s, %s, %s, %s, %s, %s)',
                        (task_id, project_id, data.get('name'), data.get('startDate'), data.get('endDate'), dependencies_json)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Verify project exists and belongs to user
                    cursor.execute('SELECT owner FROM projects WHERE id = ?', (project_id,))
                    project = cursor.fetchone()
                    
                    if not project or project[0] != username:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Project not found'})
                        return
                    
                    # Check for duplicate task name (Defect #9)
                    task_name = data.get('name', '').strip()
                    if task_name:
                        cursor.execute('SELECT COUNT(*) FROM tasks WHERE project_id = ? AND LOWER(name) = LOWER(?)', 
                                      (project_id, task_name))
                        if cursor.fetchone()[0] > 0:
                            cursor.close()
                            conn.close()
                            self.send_json(400, {'error': f'Task name "{task_name}" already exists in this project'})
                            return
                    
                    task_id = str(int(time.time() * 1000))
                    dependencies_json = json.dumps(data.get('dependencies', []))
                    
                    cursor.execute(
                        'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (?, ?, ?, ?, ?, ?)',
                        (task_id, project_id, data.get('name'), data.get('startDate'), data.get('endDate'), dependencies_json)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                
                new_task = {
                    'id': task_id,
                    'name': data.get('name'),
                    'startDate': data.get('startDate'),
                    'endDate': data.get('endDate'),
                    'dependencies': data.get('dependencies', [])
                }
                
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
                
                if USE_POSTGRES:
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
                else:
                    conn = sqlite3.connect(DB_FILE)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Verify project exists and belongs to user
                    cursor.execute('SELECT * FROM projects WHERE id = ? AND owner = ?', (project_id, username))
                    project = cursor.fetchone()
                    
                    if not project:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Project not found'})
                        return
                    
                    # Update project
                    cursor.execute(
                        'UPDATE projects SET name = ?, description = ? WHERE id = ?',
                        (data.get('name', project['name']), data.get('description', project['description']), project_id)
                    )
                    conn.commit()
                    
                    # Fetch updated project
                    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
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
                
                if USE_POSTGRES:
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
                    
                    cursor.close()
                    conn.close()
                    
                    # Normalize and return
                    self.send_json(200, self.normalize_task(dict(updated_task)))
                else:
                    conn = sqlite3.connect(DB_FILE)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Verify project exists and belongs to user
                    cursor.execute('SELECT owner FROM projects WHERE id = ?', (project_id,))
                    project = cursor.fetchone()
                    
                    if not project or project[0] != username:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Project not found'})
                        return
                    
                    # Verify task exists
                    cursor.execute('SELECT * FROM tasks WHERE id = ? AND project_id = ?', (task_id, project_id))
                    task = cursor.fetchone()
                    
                    if not task:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Task not found'})
                        return
                    
                    # Update task
                    task_dict = dict(task)
                    dependencies_json = json.dumps(data.get('dependencies', task_dict['dependencies'] if task_dict.get('dependencies') else []))
                    cursor.execute(
                        'UPDATE tasks SET name = ?, start_date = ?, end_date = ?, dependencies = ? WHERE id = ?',
                        (data.get('name', task_dict['name']), data.get('startDate', task_dict['start_date']), data.get('endDate', task_dict['end_date']), dependencies_json, task_id)
                    )
                    conn.commit()
                    
                    # Fetch updated task
                    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                    updated_task = cursor.fetchone()
                    
                    cursor.close()
                    conn.close()
                    
                    # Normalize and return
                    self.send_json(200, self.normalize_task(dict(updated_task)))
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
                if USE_POSTGRES:
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
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Verify project exists and belongs to user
                    cursor.execute('SELECT owner FROM projects WHERE id = ?', (project_id,))
                    project = cursor.fetchone()
                    
                    if not project or project[0] != username:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Project not found'})
                        return
                    
                    # Delete project (tasks will be deleted due to CASCADE)
                    cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
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
                if USE_POSTGRES:
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
                else:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Verify project exists and belongs to user
                    cursor.execute('SELECT owner FROM projects WHERE id = ?', (project_id,))
                    project = cursor.fetchone()
                    
                    if not project or project[0] != username:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Project not found'})
                        return
                    
                    # Verify task exists
                    cursor.execute('SELECT id FROM tasks WHERE id = ? AND project_id = ?', (task_id, project_id))
                    task = cursor.fetchone()
                    
                    if not task:
                        cursor.close()
                        conn.close()
                        self.send_json(404, {'error': 'Task not found'})
                        return
                    
                    # Delete task
                    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
         
        # Only allow CORS for whitelisted origins, not wildcard
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
         
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-CSRF-Token')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def translate_path(self, path):
        if path == '/' or path == '':
            path = '/index.html'
        return super().translate_path(path)

def init_database():
    """Initialize database schema on startup"""
    if USE_POSTGRES:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    advanced_mode BOOLEAN DEFAULT FALSE,
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
            
            # Create demo user if it doesn't exist
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', ('demo',))
            if cursor.fetchone()[0] == 0:
                # Create demo user
                salt = secrets.token_hex(16)
                hash_obj = hashlib.pbkdf2_hmac('sha256', 'Demo@1234'.encode(), salt.encode(), 100000)
                demo_password = f"{salt}${hash_obj.hex()}"
                
                cursor.execute(
                    'INSERT INTO users (username, password) VALUES (%s, %s)',
                    ('demo', demo_password)
                )
                
                # Create demo project
                project_id = str(int(time.time() * 1000))
                today = datetime.now().date()
                cursor.execute(
                    'INSERT INTO projects (id, owner, name, description) VALUES (%s, %s, %s, %s)',
                    (project_id, 'demo', 'Sample Project', 'This is a demo project to show how the app works')
                )
                
                # Create sample tasks
                tasks = [
                    ('Design mockups', today, today + timedelta(days=3)),
                    ('Develop backend API', today + timedelta(days=2), today + timedelta(days=7)),
                    ('Build frontend UI', today + timedelta(days=3), today + timedelta(days=10)),
                    ('Integration testing', today + timedelta(days=8), today + timedelta(days=12)),
                    ('Deploy to production', today + timedelta(days=11), today + timedelta(days=13)),
                ]
                
                for idx, (name, start, end) in enumerate(tasks):
                    task_id = str(int(time.time() * 1000) + idx)
                    cursor.execute(
                        'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (%s, %s, %s, %s, %s, %s)',
                        (task_id, project_id, name, start, end, '[]')
                    )
            
            conn.commit()
            cursor.close()
            conn.close()
            print("✓ PostgreSQL database schema initialized")
        except Exception as e:
            print(f"✗ PostgreSQL initialization error: {e}")
    else:
        # SQLite initialization
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    advanced_mode INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (owner) REFERENCES users(username)
                )
            ''')
            
            # Create tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    dependencies TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            # Create demo user if it doesn't exist
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('demo',))
            if cursor.fetchone()[0] == 0:
                # Create demo user
                salt = secrets.token_hex(16)
                hash_obj = hashlib.pbkdf2_hmac('sha256', 'Demo@1234'.encode(), salt.encode(), 100000)
                demo_password = f"{salt}${hash_obj.hex()}"
                
                cursor.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)',
                    ('demo', demo_password)
                )
                
                # Create demo project
                project_id = str(int(time.time() * 1000))
                today = datetime.now().date()
                cursor.execute(
                    'INSERT INTO projects (id, owner, name, description) VALUES (?, ?, ?, ?)',
                    (project_id, 'demo', 'Sample Project', 'This is a demo project to show how the app works')
                )
                
                # Create sample tasks
                tasks = [
                    ('Design mockups', today, today + timedelta(days=3)),
                    ('Develop backend API', today + timedelta(days=2), today + timedelta(days=7)),
                    ('Build frontend UI', today + timedelta(days=3), today + timedelta(days=10)),
                    ('Integration testing', today + timedelta(days=8), today + timedelta(days=12)),
                    ('Deploy to production', today + timedelta(days=11), today + timedelta(days=13)),
                ]
                
                for idx, (name, start, end) in enumerate(tasks):
                    task_id = str(int(time.time() * 1000) + idx)
                    cursor.execute(
                        'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (?, ?, ?, ?, ?, ?)',
                        (task_id, project_id, name, start, end, '[]')
                    )
            
            conn.commit()
            print("✓ SQLite database schema initialized")
        except Exception as e:
            print(f"✗ SQLite initialization error: {e}")
        finally:
            cursor.close()
            conn.close()

def hash_password_standalone(password):
    """Hash password with salt (standalone version for use during initialization)"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"

def load_critical_users():
    """Load critical users from config file"""
    try:
        if os.path.exists(USERS_CONFIG_FILE):
            with open(USERS_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('critical_users', [])
    except Exception as e:
        print(f"⚠ Could not load critical users config: {e}")
    return []

def recreate_critical_users():
    """Recreate critical users if they're missing (database reset recovery)"""
    critical_users = load_critical_users()
    if not critical_users:
        return
    
    try:
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            for user_config in critical_users:
                username = user_config['username']
                password = user_config['password']
                
                # Check if user exists
                cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', (username,))
                if cursor.fetchone()[0] == 0:
                    # User is missing - recreate it
                    try:
                        hashed_password = hash_password_standalone(password)
                        cursor.execute(
                            'INSERT INTO users (username, password) VALUES (%s, %s)',
                            (username, hashed_password)
                        )
                        conn.commit()
                        print(f"✓ Recreated critical user: {username}")
                    except Exception as e:
                        conn.rollback()
                        print(f"⚠ Could not recreate user {username}: {e}")
            
            cursor.close()
            conn.close()
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            for user_config in critical_users:
                username = user_config['username']
                password = user_config['password']
                
                cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
                if cursor.fetchone()[0] == 0:
                    try:
                        hashed_password = hash_password_standalone(password)
                        cursor.execute(
                            'INSERT INTO users (username, password) VALUES (?, ?)',
                            (username, hashed_password)
                        )
                        conn.commit()
                        print(f"✓ Recreated critical user: {username}")
                    except Exception as e:
                        conn.rollback()
                        print(f"⚠ Could not recreate user {username}: {e}")
            
            conn.close()
    except Exception as e:
        print(f"⚠ Error recreating critical users: {e}")

def verify_database_integrity():
    """Verify database has expected users and structure"""
    try:
        if USE_POSTGRES:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Check demo user exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', ('demo',))
            demo_count = cursor.fetchone()[0]
            
            # Check users table has data
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Check projects table
            cursor.execute('SELECT COUNT(*) FROM projects')
            total_projects = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✓ Database integrity: {total_users} users, {total_projects} projects")
            if demo_count == 0:
                print("⚠ WARNING: demo user not found - database may have been reset! Attempting recovery...")
            # Always check and recreate critical users if missing
            recreate_critical_users()
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('demo',))
            demo_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM projects')
            total_projects = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✓ Database integrity: {total_users} users, {total_projects} projects")
            # Always check and recreate critical users if missing
            recreate_critical_users()
    except Exception as e:
        print(f"⚠ Database integrity check failed: {e}")

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Verify database integrity after initialization
    verify_database_integrity()
    
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    server = HTTPServer((host, port), AuthHandler)
    print(f'Server running at http://{host}:{port}')
    print('Press Ctrl+C to stop')
    server.serve_forever()
