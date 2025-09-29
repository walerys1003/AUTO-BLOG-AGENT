import os
from functools import wraps
from flask import session, request, redirect, url_for, render_template_string, flash
from werkzeug.security import check_password_hash, generate_password_hash

class AdminAuth:
    """Simple admin authentication system using environment variables"""
    
    def __init__(self):
        self.admin_login = os.environ.get("ADMIN_LOGIN")
        self.admin_password = os.environ.get("ADMIN_PASSWORD")
        
        if not self.admin_login or not self.admin_password:
            raise ValueError("ADMIN_LOGIN and ADMIN_PASSWORD environment variables are required")
    
    def authenticate(self, username, password):
        """Authenticate admin user"""
        return (username == self.admin_login and password == self.admin_password)
    
    def login_user(self):
        """Log in the admin user"""
        session['admin_logged_in'] = True
        session['admin_username'] = self.admin_login
    
    def logout_user(self):
        """Log out the admin user"""
        session.pop('admin_logged_in', None)
        session.pop('admin_username', None)
    
    def is_authenticated(self):
        """Check if admin is authenticated"""
        return session.get('admin_logged_in', False)

# Global admin auth instance
admin_auth = AdminAuth()

def require_admin_login(f):
    """Decorator to require admin authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not admin_auth.is_authenticated():
            # Store the URL they were trying to access
            session['next_url'] = request.url
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Login template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - Blog Automation Agent</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { 
            background: linear-gradient(135deg, #287F71, #EB862A);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            padding: 2rem;
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo i {
            font-size: 3rem;
            color: #287F71;
        }
        .btn-admin {
            background: #287F71;
            border: none;
            width: 100%;
            padding: 12px;
            font-weight: 600;
        }
        .btn-admin:hover {
            background: #1f6b5e;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <i class="fas fa-robot"></i>
            <h3 class="mt-3 text-dark">Blog Automation Agent</h3>
            <p class="text-muted">Administrator Login</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="alert alert-danger">
                    {% for message in messages %}
                        {{ message }}
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <form method="POST">
            <div class="mb-3">
                <label for="username" class="form-label">
                    <i class="fas fa-user"></i> Login Administratora
                </label>
                <input type="text" class="form-control" id="username" name="username" required>
            </div>
            
            <div class="mb-3">
                <label for="password" class="form-label">
                    <i class="fas fa-lock"></i> Hasło Administratora
                </label>
                <input type="password" class="form-control" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn btn-admin btn-primary">
                <i class="fas fa-sign-in-alt"></i> Zaloguj jako Administrator
            </button>
        </form>
        
        <div class="text-center mt-3">
            <small class="text-muted">
                <i class="fas fa-shield-alt"></i> 
                Dostęp tylko dla upoważnionego administratora
            </small>
        </div>
    </div>
</body>
</html>
"""