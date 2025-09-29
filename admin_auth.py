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
        :root {
            --primary-color: #287F71;
            --secondary-color: #EB862A;
            --dark-color: #0a0f1c;
        }
        body { 
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            min-height: 100vh;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
        }
        .main-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .copy-section {
            color: white;
            padding: 3rem 2rem;
        }
        .copy-section h1 {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1.5rem;
        }
        .copy-section .lead {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.95;
        }
        .feature-list {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 0.5rem 0;
            font-size: 1.1rem;
        }
        .feature-list i {
            color: var(--secondary-color);
            margin-right: 0.5rem;
            width: 20px;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            margin: 2rem;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo i {
            font-size: 3rem;
            color: var(--primary-color);
        }
        .btn-admin {
            background: var(--primary-color);
            border: none;
            width: 100%;
            padding: 15px;
            font-weight: 600;
            border-radius: 8px;
            font-size: 1.1rem;
        }
        .btn-admin:hover {
            background: #1f6b5e;
            transform: translateY(-1px);
        }
        .form-control {
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            font-size: 1rem;
        }
        .form-control:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.2rem rgba(40, 127, 113, 0.25);
        }
        .form-label {
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 0.5rem;
        }
        @media (max-width: 768px) {
            .copy-section {
                padding: 2rem 1rem;
                text-align: center;
            }
            .copy-section h1 {
                font-size: 2rem;
            }
            .login-container {
                margin: 1rem;
                padding: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container-fluid main-container">
        <div class="row w-100">
            <!-- Copy section - lewa strona -->
            <div class="col-lg-7 col-md-6 copy-section d-flex align-items-center">
                <div>
                    <h1>
                        <i class="fas fa-robot me-2"></i>
                        Blog Automation Agent
                    </h1>
                    <p class="lead">
                        Zaawansowany system automatyzacji WordPress dla profesjonalnego zarządzania treścią
                    </p>
                    
                    <ul class="feature-list">
                        <li>
                            <i class="fas fa-magic"></i>
                            <strong>AI-powered generowanie treści</strong> - Claude & GPT-4 via OpenRouter
                        </li>
                        <li>
                            <i class="fas fa-clock"></i>
                            <strong>Batch Generation</strong> - wydajne poranne sesje publikacji
                        </li>
                        <li>
                            <i class="fas fa-wordpress"></i>
                            <strong>Multi-blog management</strong> - zarządzanie wieloma blogami WordPress
                        </li>
                        <li>
                            <i class="fas fa-images"></i>
                            <strong>Automatyczne obrazy</strong> - integracja z Unsplash & Google Images
                        </li>
                        <li>
                            <i class="fas fa-search"></i>
                            <strong>SEO Optimization</strong> - 12 tagów, meta descriptions, keywords
                        </li>
                        <li>
                            <i class="fas fa-users"></i>
                            <strong>Author Rotation</strong> - rotacja autorów dla naturalności
                        </li>
                        <li>
                            <i class="fas fa-share-alt"></i>
                            <strong>Social Media</strong> - automatyczna promocja w mediach społecznościowych
                        </li>
                        <li>
                            <i class="fas fa-chart-line"></i>
                            <strong>Analytics & Reports</strong> - szczegółowe raporty wydajności
                        </li>
                    </ul>
                </div>
            </div>
            
            <!-- Login section - prawa strona -->
            <div class="col-lg-5 col-md-6 d-flex align-items-center justify-content-center">
                <div class="login-container">
                    <div class="logo">
                        <i class="fas fa-shield-alt"></i>
                        <h3 class="mt-3 text-dark">Panel Administratora</h3>
                        <p class="text-muted">Zaloguj się aby uzyskać dostęp</p>
                    </div>
                    
                    {% with messages = get_flashed_messages() %}
                        {% if messages %}
                            <div class="alert alert-danger">
                                {% for message in messages %}
                                    <i class="fas fa-exclamation-triangle me-2"></i>{{ message }}
                                {% endfor %}
                            </div>
                        {% endif %}
                    {% endwith %}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label for="username" class="form-label">
                                <i class="fas fa-user me-1"></i> Login Administratora
                            </label>
                            <input type="text" class="form-control" id="username" name="username" required placeholder="Wprowadź login">
                        </div>
                        
                        <div class="mb-4">
                            <label for="password" class="form-label">
                                <i class="fas fa-lock me-1"></i> Hasło Administratora
                            </label>
                            <input type="password" class="form-control" id="password" name="password" required placeholder="Wprowadź hasło">
                        </div>
                        
                        <button type="submit" class="btn btn-admin btn-primary">
                            <i class="fas fa-sign-in-alt me-2"></i> Zaloguj do systemu
                        </button>
                    </form>
                    
                    <div class="text-center mt-4">
                        <small class="text-muted">
                            <i class="fas fa-shield-alt me-1"></i> 
                            Dostęp tylko dla upoważnionego administratora systemu
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""