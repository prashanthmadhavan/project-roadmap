#!/usr/bin/env python3
"""
Script to create GitHub repository and push code using GitHub API
"""

import json
import subprocess
import getpass
import sys

def create_github_repo(username, token):
    """Create GitHub repository using API"""
    import urllib.request
    import base64
    
    repo_name = "project-roadmap"
    
    # GitHub API endpoint
    url = "https://api.github.com/user/repos"
    
    # Prepare request
    payload = {
        "name": repo_name,
        "description": "Interactive task management with Gantt chart visualization",
        "homepage": f"https://github.com/{username}/{repo_name}",
        "public": True,
        "auto_init": False
    }
    
    # Create auth header
    credentials = base64.b64encode(f"{username}:{token}".encode()).decode()
    
    # Make request
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.v3+json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode())
            if "id" in result:
                print(f"✓ Repository created: {result['html_url']}")
                return True
            else:
                print(f"✗ Error: {result.get('message', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"✗ Error creating repository: {e}")
        return False

def push_to_github(username):
    """Push code to GitHub using SSH"""
    try:
        # Test SSH connection
        subprocess.run(["ssh", "-T", "git@github.com"], 
                      capture_output=True, text=True, timeout=5)
        
        # Configure remote
        subprocess.run(["git", "remote", "remove", "origin"], 
                      capture_output=True)
        
        repo_url = f"git@github.com:{username}/project-roadmap.git"
        subprocess.run(["git", "remote", "add", "origin", repo_url], 
                      check=True)
        
        # Push
        print("\nPushing code to GitHub...")
        result = subprocess.run(["git", "push", "-u", "origin", "main"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Code pushed successfully!")
            print(f"✓ Repository: https://github.com/{username}/project-roadmap")
            return True
        else:
            print(f"✗ Push failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("GitHub Repository Creation & Push")
    print("=" * 60)
    
    username = input("\nEnter GitHub username: ").strip()
    
    print("\n--- Creating Repository ---")
    print("Do you want to use GitHub API to create the repo?")
    print("(You'll need a Personal Access Token with 'repo' scope)")
    use_api = input("\nUse GitHub API? (y/n) [n]: ").strip().lower() == 'y'
    
    if use_api:
        print("\nVisit https://github.com/settings/tokens to create a token:")
        print("- Select 'repo' scope")
        print("- Copy the token")
        token = getpass.getpass("\nPaste your GitHub token: ")
        
        if not create_github_repo(username, token):
            sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("Manual Repository Creation")
        print("=" * 60)
        print("\nPlease create the repository manually:")
        print("1. Visit: https://github.com/new")
        print("2. Repository name: project-roadmap")
        print("3. Description: Interactive task management with Gantt chart")
        print("4. Visibility: Public")
        print("5. Do NOT initialize with README, .gitignore, or license")
        print("6. Click 'Create repository'")
        print("\n" + "=" * 60)
        input("Press Enter when done...")
    
    if push_to_github(username):
        print("\n" + "=" * 60)
        print("✓ SUCCESS!")
        print("=" * 60)
        print(f"\nYour repository is now live at:")
        print(f"https://github.com/{username}/project-roadmap")
        print(f"\nTo deploy and host:")
        print("1. Read DEPLOYMENT.md for hosting options")
        print("2. Recommended: Deploy to Render.com or Railway.app")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("- Check your GitHub username is correct")
        print("- Verify SSH key is added to GitHub")
        print("- Try: ssh -T git@github.com")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
