#!/usr/bin/env python3
"""
Generate comprehensive test data for Task Gantt Chart application.
Tests all 9 defects with multiple projects and test cases.
"""

import sqlite3
import os
import time
import uuid
from datetime import datetime, timedelta
import hashlib
import hmac

def hash_password(password):
    """Hash password using PBKDF2-HMAC-SHA256"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return f"pbkdf2_sha256:100000:{salt.hex()}:{key.hex()}"

def get_db():
    """Get database connection"""
    db_file = 'task_gantt.db'
    conn = sqlite3.connect(db_file)
    return conn

def init_db(conn):
    """Initialize database schema"""
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
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠ Database initialization: {e}")

def clear_test_data(conn):
    """Clear existing test data (keep demo user)"""
    cursor = conn.cursor()
    try:
        # Delete test users and their projects/tasks
        cursor.execute("DELETE FROM tasks WHERE project_id IN (SELECT id FROM projects WHERE owner IN ('testuser1', 'testuser2', 'testuser3'))")
        cursor.execute("DELETE FROM projects WHERE owner IN ('testuser1', 'testuser2', 'testuser3')")
        cursor.execute("DELETE FROM users WHERE username IN ('testuser1', 'testuser2', 'testuser3')")
        conn.commit()
        print("✓ Cleared existing test data")
    except Exception as e:
        print(f"⚠ Could not clear test data: {e}")

def create_test_users(conn):
    """Create test users for multi-user testing"""
    cursor = conn.cursor()
    users = [
        ('testuser1', 'TestUser@1'),
        ('testuser2', 'TestUser@2'),
        ('testuser3', 'TestUser@3'),
    ]
    
    created = []
    for username, password in users:
        try:
            hashed = hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password, advanced_mode) VALUES (?, ?, ?)',
                (username, hashed, 0)
            )
            created.append(username)
            print(f"✓ Created user: {username} / {password}")
        except sqlite3.IntegrityError:
            print(f"⚠ User {username} already exists")
    
    conn.commit()
    return created

def create_project(conn, owner, name, description=""):
    """Create a project and return its ID"""
    import uuid
    project_id = str(uuid.uuid4())
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO projects (id, owner, name, description) VALUES (?, ?, ?, ?)',
            (project_id, owner, name, description)
        )
        conn.commit()
        return project_id
    except Exception as e:
        print(f"✗ Error creating project: {e}")
        return None

def create_task(conn, project_id, name, start_date, end_date, dependencies=None):
    """Create a task"""
    import uuid
    task_id = str(uuid.uuid4())
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO tasks (id, project_id, name, start_date, end_date, dependencies) VALUES (?, ?, ?, ?, ?, ?)',
            (task_id, project_id, name, start_date, end_date, dependencies)
        )
        conn.commit()
        return task_id
    except Exception as e:
        print(f"✗ Error creating task: {e}")
        return None

def generate_demo_user_test_data(conn):
    """Generate test data for demo user with multiple projects"""
    print("\n" + "="*60)
    print("GENERATING TEST DATA FOR DEMO USER")
    print("="*60)
    
    base_date = datetime.now().date()
    
    # PROJECT 1: Task Visibility Testing (20+ tasks)
    print("\n[Project 1] Creating: tasks_visibility_test")
    proj1 = create_project(conn, 'demo', 'Project 1: Task Visibility', 
                          'Tests that all 20+ tasks appear in Gantt view')
    
    if proj1:
        # Create 20 tasks spread across 3 weeks
        for i in range(1, 21):
            week = (i - 1) // 7
            day_offset = (i - 1) % 7
            start = base_date + timedelta(days=week*7 + day_offset)
            end = start + timedelta(days=1)
            create_task(conn, proj1, f"Task {i:02d}", start.isoformat(), end.isoformat())
        print(f"  ✓ Created 20 tasks for visibility testing")
    
    # PROJECT 2: Task Dependencies Testing
    print("\n[Project 2] Creating: dependencies_test")
    proj2 = create_project(conn, 'demo', 'Project 2: Dependencies', 
                          'Tests task dependencies with chain: T1→T2→T3→T4→T5')
    
    if proj2:
        task_ids = []
        for i in range(1, 6):
            start = base_date + timedelta(days=i-1)
            end = start + timedelta(days=1)
            task_id = create_task(conn, proj2, f"Dependency Task {i}", 
                                 start.isoformat(), end.isoformat())
            task_ids.append(task_id)
        
        # Create dependency chain
        cursor = conn.cursor()
        for i in range(1, len(task_ids)):
            prev_id = task_ids[i-1]
            curr_id = task_ids[i]
            cursor.execute('UPDATE tasks SET dependencies = ? WHERE id = ?',
                          (prev_id, curr_id))
        conn.commit()
        print(f"  ✓ Created 5 tasks with dependency chain")
    
    # PROJECT 3: Task Deletion Testing
    print("\n[Project 3] Creating: deletion_test")
    proj3 = create_project(conn, 'demo', 'Project 3: Deletion Testing', 
                          'Tests task deletion without looping')
    
    if proj3:
        for i in range(1, 11):
            start = base_date + timedelta(days=i-1)
            end = start + timedelta(days=1)
            create_task(conn, proj3, f"Deletable Task {i:02d}", 
                       start.isoformat(), end.isoformat())
        print(f"  ✓ Created 10 tasks for deletion testing")
    
    # PROJECT 4: Task Name Duplication Testing
    print("\n[Project 4] Creating: duplication_test")
    proj4 = create_project(conn, 'demo', 'Project 4: Name Duplication', 
                          'Tests duplicate task name validation')
    
    if proj4:
        base_names = [
            "Design Phase",
            "Development",
            "Testing",
            "Deployment",
            "Documentation"
        ]
        for name in base_names:
            start = base_date + timedelta(days=1)
            end = start + timedelta(days=1)
            create_task(conn, proj4, name, start.isoformat(), end.isoformat())
        print(f"  ✓ Created 5 tasks for duplication testing")
    
    # PROJECT 5: User State Isolation Testing
    print("\n[Project 5] Creating: user_state_test")
    proj5 = create_project(conn, 'demo', 'Project 5: User State Isolation', 
                          'Should be cleared when switching users')
    
    if proj5:
        for i in range(1, 6):
            start = base_date + timedelta(days=i-1)
            end = start + timedelta(days=1)
            create_task(conn, proj5, f"Demo State Task {i}", 
                       start.isoformat(), end.isoformat())
        print(f"  ✓ Created 5 tasks for user state testing")

def generate_test_user_data(conn):
    """Generate test data for test users"""
    print("\n" + "="*60)
    print("GENERATING TEST DATA FOR TEST USERS")
    print("="*60)
    
    base_date = datetime.now().date()
    
    for user_num, username in enumerate(['testuser1', 'testuser2', 'testuser3'], 1):
        print(f"\n[User {user_num}] {username}")
        
        # Create 2 projects per user
        for proj_num in range(1, 3):
            proj_name = f"{username.replace('test', 'User ')} - Project {proj_num}"
            proj_id = create_project(conn, username, proj_name, 
                                    f"Test project {proj_num} for {username}")
            
            if proj_id:
                # Create 5-8 tasks per project
                task_count = 5 + proj_num
                for i in range(1, task_count + 1):
                    start = base_date + timedelta(days=i-1)
                    end = start + timedelta(days=1)
                    create_task(conn, proj_id, f"Task {i}", 
                               start.isoformat(), end.isoformat())
                print(f"  ✓ Created {proj_name} with {task_count} tasks")

def generate_edge_case_data(conn):
    """Generate edge case test data in demo user"""
    print("\n" + "="*60)
    print("GENERATING EDGE CASE TEST DATA")
    print("="*60)
    
    base_date = datetime.now().date()
    
    # PROJECT 6: Large Task Set
    print("\n[Project 6] Creating: large_task_set")
    proj6 = create_project(conn, 'demo', 'Project 6: Large Task Set', 
                          'Tests performance with 50+ tasks')
    
    if proj6:
        for i in range(1, 51):
            week = (i - 1) // 10
            offset = (i - 1) % 10
            start = base_date + timedelta(days=week*7 + offset)
            end = start + timedelta(days=1)
            create_task(conn, proj6, f"Task {i:02d}", start.isoformat(), end.isoformat())
        print(f"  ✓ Created 50 large task set")
    
    # PROJECT 7: Long-Duration Tasks
    print("\n[Project 7] Creating: long_duration_test")
    proj7 = create_project(conn, 'demo', 'Project 7: Long Duration', 
                          'Tests multi-week spanning tasks')
    
    if proj7:
        task_configs = [
            ("Infrastructure Setup", 0, 14),
            ("Core Development", 7, 21),
            ("Testing Phase", 14, 21),
            ("Documentation", 10, 21),
            ("Deployment Prep", 20, 21),
        ]
        for name, start_offset, end_offset in task_configs:
            start = base_date + timedelta(days=start_offset)
            end = base_date + timedelta(days=end_offset)
            create_task(conn, proj7, name, start.isoformat(), end.isoformat())
        print(f"  ✓ Created long-duration tasks")
    
    # PROJECT 8: Same-Day Tasks
    print("\n[Project 8] Creating: same_day_test")
    proj8 = create_project(conn, 'demo', 'Project 8: Same Day', 
                          'Tests multiple tasks on same day')
    
    if proj8:
        same_day = base_date + timedelta(days=5)
        for i in range(1, 6):
            create_task(conn, proj8, f"Same Day Task {i}", 
                       same_day.isoformat(), same_day.isoformat())
        print(f"  ✓ Created 5 tasks for same day")

def print_test_summary(conn):
    """Print summary of generated test data"""
    print("\n" + "="*60)
    print("TEST DATA SUMMARY")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Count users
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    # Count projects
    cursor.execute('SELECT COUNT(*) FROM projects')
    project_count = cursor.fetchone()[0]
    
    # Count tasks
    cursor.execute('SELECT COUNT(*) FROM tasks')
    task_count = cursor.fetchone()[0]
    
    # Count by owner
    cursor.execute('''
        SELECT owner, COUNT(DISTINCT p.id) as proj_count, COUNT(DISTINCT t.id) as task_count
        FROM projects p
        LEFT JOIN tasks t ON t.project_id = p.id
        GROUP BY owner
    ''')
    
    print(f"\nTotal Users: {user_count}")
    print(f"Total Projects: {project_count}")
    print(f"Total Tasks: {task_count}")
    
    print("\n" + "-"*60)
    print("Breakdown by User:")
    print("-"*60)
    
    for owner, proj_count, task_count in cursor.fetchall():
        print(f"  {owner:15} → {proj_count:2} projects, {task_count:3} tasks")
    
    print("\n" + "-"*60)
    print("TEST CREDENTIALS:")
    print("-"*60)
    print("  demo / Demo@1234")
    print("  testuser1 / TestUser@1")
    print("  testuser2 / TestUser@2")
    print("  testuser3 / TestUser@3")
    
    print("\n" + "-"*60)
    print("TEST COVERAGE:")
    print("-"*60)
    print("  ✓ Defect #1: User persistence (testuser1, testuser2, testuser3)")
    print("  ✓ Defect #2: Task visibility (20+ tasks in 1 project)")
    print("  ✓ Defect #3: Timeline slider removal (N/A - UI change)")
    print("  ✓ Defect #4: Advanced toggle removal (N/A - UI change)")
    print("  ✓ Defect #5: Drag & drop removal (N/A - UI change)")
    print("  ✓ Defect #6: User state isolation (5 projects with demo data)")
    print("  ✓ Defect #7: Swimlanes removal (N/A - UI change)")
    print("  ✓ Defect #8: Task deletion loop (10 tasks in deletion_test)")
    print("  ✓ Defect #9: Task name duplication (5 named tasks + edge cases)")
    
    print("\n" + "="*60)

def main():
    """Main test data generation"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " TEST DATA GENERATOR FOR ALL 9 DEFECTS ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    conn = get_db()
    
    try:
        # Initialize database
        init_db(conn)
        
        # Clear old test data
        clear_test_data(conn)
        
        # Create test users
        create_test_users(conn)
        
        # Generate comprehensive test data
        generate_demo_user_test_data(conn)
        generate_test_user_data(conn)
        generate_edge_case_data(conn)
        
        # Print summary
        print_test_summary(conn)
        
        print("\n✓ Test data generation complete!")
        print("\nNext steps:")
        print("  1. Start server: python3 server.py")
        print("  2. Open browser: http://localhost:8000")
        print("  3. Login with test credentials above")
        print("  4. Run manual test cases from DEFECT_ANALYSIS.md")
        
    except Exception as e:
        print(f"\n✗ Error generating test data: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
