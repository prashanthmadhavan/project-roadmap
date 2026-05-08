# Authentication Feature Guide

## Overview

The Task Gantt Chart application now includes a secure user authentication system. Each user has their own account and can only see projects and tasks they created.

---

## Password Requirements

When creating an account, passwords must meet these requirements:

### Mandatory Rules
✅ **Minimum 8 characters** - Password must be at least 8 characters long  
✅ **Uppercase letters** - Must contain at least one uppercase letter (A-Z)  
✅ **Lowercase letters** - Must contain at least one lowercase letter (a-z)  
✅ **Case sensitive** - Passwords are case-sensitive (e.g., "Password123" ≠ "password123")

### Examples of Valid Passwords
- `MyProject2024`
- `Test@Password99`
- `SecurePass123`
- `GanttChart456`

### Examples of Invalid Passwords
- `password123` ❌ (no uppercase)
- `PASSWORD123` ❌ (no lowercase)
- `Pass123` ❌ (only 7 characters)
- `12345678` ❌ (no letters)

---

## Account Creation

### Step 1: Go to Registration Page
1. Visit your application URL
2. Click **"Create one"** on the login page

### Step 2: Enter Credentials
1. **Username**: Choose a unique username (minimum 3 characters)
2. **Password**: Enter a password meeting all requirements
   - Real-time validation shows which requirements are met
   - Green checkmarks ✅ appear as you satisfy each requirement

### Step 3: Create Account
- Click **"Create Account"** button
- You'll be logged in automatically
- Your user account is now created

---

## Login

### Sign In to Your Account
1. Enter your **Username**
2. Enter your **Password** (case-sensitive!)
3. Click **"Sign In"**

### What Happens After Login
- You see your personal dashboard
- All your projects and tasks appear
- Your username displays in the top-right corner
- You can now manage your projects

---

## Important Notes

### No Password Recovery
⚠️ **IMPORTANT**: There is **no way to recover a forgotten password**.

If you forget your password:
- Your account is locked
- A new account must be created with a different username
- You will lose access to all projects under that username
- **Make sure to remember your password!**

### Password Security
- Passwords are hashed with PBKDF2 and salt
- Never stored in plain text
- Even administrators cannot see your actual password
- Only you know your password

### Session Management
- Sessions are stored in browser's localStorage
- Logging out clears your session token
- You must login again to access your account
- Closing the browser doesn't automatically log you out

---

## User Data Isolation

### Private Projects
- Each user can only see their own projects
- Other users cannot see, edit, or delete your projects
- Projects are completely isolated by user

### Persistent Data
- Your account and projects are stored permanently
- Data survives:
  - Application restarts
  - Server deployments
  - Browser closures
- Your data is not erased unless explicitly deleted

### Logout
To logout:
1. Click the **"Logout"** button in the top-right corner
2. You're returned to the login page
3. All session data is cleared
4. Your projects remain saved for next login

---

## Account Management

### Change Your Settings
Currently, the following can be managed:
- ✅ Create projects
- ✅ Create and manage tasks
- ✅ Delete your projects
- ✅ Logout

### What Cannot Be Changed
- ❌ Username (permanent)
- ❌ Password (no change password feature)
- ❌ Email (not implemented)

### Delete Your Account
To delete your account and all associated data:
1. Delete all your projects one by one
2. Account remains but with no projects
3. There is no bulk delete account option

---

## API Authentication

### For Developers

All protected API endpoints require authentication:

```
Authorization: Bearer <token>
```

### Get Authentication Token

**Register/Create Account**:
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "myusername",
  "password": "MyPassword123"
}

Response:
{
  "username": "myusername",
  "token": "token_string_here",
  "message": "Account created successfully"
}
```

**Login**:
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "myusername",
  "password": "MyPassword123"
}

Response:
{
  "username": "myusername",
  "token": "token_string_here",
  "message": "Logged in successfully"
}
```

### Use Token for Protected Endpoints

```bash
GET /api/projects
Authorization: Bearer token_string_here

GET /api/auth/me
Authorization: Bearer token_string_here
```

### Token Expiration
- Tokens last for the current session
- Tokens are cleared on logout
- No automatic token expiration
- New token needed after logout/login

---

## Security Features

### Password Hashing
- PBKDF2 with 100,000 iterations
- Unique salt per password
- Even if database is compromised, passwords are safe

### Case Sensitivity
- Passwords are case-sensitive
- Usernames are case-sensitive
- "john" ≠ "John"

### Secure Transmission
- Use HTTPS in production (Render handles this)
- Tokens sent in Authorization header
- No credentials in URL

---

## Troubleshooting

### "Invalid username or password"
- Check username is spelled correctly
- Verify password is correct (case-sensitive!)
- Usernames and passwords are case-sensitive

### "Username already exists"
- Username is taken
- Choose a different username

### "Password must contain uppercase letters"
- Add uppercase letters (A-Z) to your password
- Example: "aBcDeFgH1"

### "Password must contain lowercase letters"
- Add lowercase letters (a-z) to your password
- Example: "AbCdEfGh1"

### "Password must be at least 8 characters"
- Make password longer
- Minimum: 8 characters

### Can't login after creating account
- Make sure you waited for the success message
- Try logging in with your new credentials
- Check that caps lock is not on

### Session expires when I close the browser
- This is normal behavior
- Simply log back in
- Your projects are saved and waiting

---

## Best Practices

1. **Use Strong Passwords**
   - Don't use predictable patterns
   - Mix uppercase, lowercase, numbers, and symbols (if allowed)
   - Avoid personal information

2. **Remember Your Password**
   - No password recovery available
   - Write it down somewhere safe
   - Use a password manager if available

3. **Keep Your Account Safe**
   - Don't share your password
   - Log out when using shared computers
   - Don't use the same password elsewhere

4. **Backup Important Data**
   - Your projects are permanently saved
   - No backup feature available
   - Be careful when deleting projects

---

## Data Stored Per User

### User Account
- Username (unique)
- Hashed password
- Account creation date

### User Projects
- Project ID
- Project name
- Project description
- Creation date
- All associated tasks

### User Tasks
- Task ID
- Task name
- Start date
- End date
- Task dependencies

---

## Frequently Asked Questions

**Q: Can I reset my password?**  
A: No. If you forget your password, you must create a new account.

**Q: Can an admin reset my password?**  
A: No. There are no admin accounts in this system.

**Q: What happens if I delete my account?**  
A: Just delete all your projects. The empty account remains.

**Q: Can I see other users' projects?**  
A: No. You can only see projects you created.

**Q: Are passwords encrypted?**  
A: Yes. Passwords are hashed with PBKDF2-HMAC-SHA256.

**Q: Is my data backed up?**  
A: Data is stored on the server and persists across restarts.

**Q: Can I change my username?**  
A: No. Usernames are permanent.

**Q: What if I mistype my username?**  
A: You'll get "Invalid username or password" error.

---

## Support

For issues with authentication or account management:

1. Check this guide for common problems
2. Review the password requirements
3. Try logging out and back in
4. Check your browser's developer console for errors

---

**Version**: 3.0 (Authentication Update)  
**Last Updated**: May 2026
