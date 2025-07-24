from flask import request, jsonify, render_template, Blueprint
from app import app, db
from models import Blog, Category, AutomationRule, ContentLog
from datetime import datetime
import json
import requests
from requests.auth import HTTPBasicAuth

# Create blueprint for multi-blog management
multi_blog_bp = Blueprint('multi_blog', __name__)

@multi_blog_bp.route('/multi-blog')
def multi_blog_management():
    """Multi-blog management interface"""
    return render_template('multi_blog_management.html')


@multi_blog_bp.route('/api/blogs', methods=['GET'])
def get_blogs():
    """Get all blogs with stats"""
    try:
        blogs = Blog.query.all()
        blog_data = []
        
        for blog in blogs:
            # Get blog statistics
            categories_count = Category.query.filter_by(blog_id=blog.id).count()
            articles_count = ContentLog.query.filter_by(blog_id=blog.id).count()
            
            # Get automation rules
            automation_rules = AutomationRule.query.filter_by(blog_id=blog.id).all()
            rules_data = []
            daily_articles = 0
            
            for rule in automation_rules:
                rules_data.append({
                    'id': rule.id,
                    'name': rule.name,
                    'is_active': rule.is_active,
                    'posts_per_day': rule.posts_per_day,
                    'min_interval_hours': rule.min_interval_hours
                })
                if rule.is_active:
                    daily_articles += rule.posts_per_day
            
            blog_info = {
                'id': blog.id,
                'name': blog.name,
                'url': blog.url,
                'api_url': blog.api_url,
                'username': blog.username,
                'active': blog.active,
                'approval_required': blog.approval_required,
                'created_at': blog.created_at.isoformat() if blog.created_at else None,
                'categories_count': categories_count,
                'articles_count': articles_count,
                'rules_count': len(automation_rules),
                'daily_articles': daily_articles,
                'automation_rules': rules_data
            }
            blog_data.append(blog_info)
        
        return jsonify({
            'success': True,
            'blogs': blog_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania blogów: {str(e)}'
        }), 500


@multi_blog_bp.route('/api/blogs', methods=['POST'])
def add_blog():
    """Add new blog"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'url', 'api_url', 'username', 'api_token']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Pole {field} jest wymagane'
                }), 400
        
        # Check if blog with this name already exists
        existing_blog = Blog.query.filter_by(name=data['name']).first()
        if existing_blog:
            return jsonify({
                'success': False,
                'message': f'Blog o nazwie {data["name"]} już istnieje'
            }), 400
        
        # Test WordPress API connection if blog is set to active
        if data.get('active', False):
            test_result = test_wordpress_connection(
                data['api_url'], 
                data['username'], 
                data['api_token']
            )
            if not test_result['success']:
                return jsonify({
                    'success': False,
                    'message': f'Nie można połączyć z WordPress API: {test_result["message"]}'
                }), 400
        
        # Create new blog
        new_blog = Blog(
            name=data['name'],
            url=data['url'],
            api_url=data['api_url'],
            username=data['username'],
            api_token=data['api_token'],
            active=data.get('active', False),
            approval_required=data.get('approval_required', False),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_blog)
        db.session.commit()
        
        # If active, sync categories
        if new_blog.active:
            sync_result = sync_blog_categories(new_blog.id)
            if sync_result['success']:
                create_default_automation_rule(new_blog.id)
        
        return jsonify({
            'success': True,
            'message': f'Blog {data["name"]} został dodany pomyślnie',
            'blog_id': new_blog.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas dodawania bloga: {str(e)}'
        }), 500


@multi_blog_bp.route('/api/blogs/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    """Get specific blog details"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        
        blog_data = {
            'id': blog.id,
            'name': blog.name,
            'url': blog.url,
            'api_url': blog.api_url,
            'username': blog.username,
            'active': blog.active,
            'approval_required': blog.approval_required,
            'created_at': blog.created_at.isoformat() if blog.created_at else None
        }
        
        return jsonify({
            'success': True,
            'blog': blog_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas pobierania bloga: {str(e)}'
        }), 500


@multi_blog_bp.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    """Update blog details"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        data = request.get_json()
        
        # Test connection if credentials changed or blog is being activated
        if (data.get('active', False) and not blog.active) or data.get('api_token'):
            api_token = data.get('api_token', blog.api_token)
            username = data.get('username', blog.username)
            api_url = data.get('api_url', blog.api_url)
            
            test_result = test_wordpress_connection(api_url, username, api_token)
            if not test_result['success']:
                return jsonify({
                    'success': False,
                    'message': f'Nie można połączyć z WordPress API: {test_result["message"]}'
                }), 400
        
        # Update blog fields
        if 'name' in data:
            blog.name = data['name']
        if 'url' in data:
            blog.url = data['url']
        if 'api_url' in data:
            blog.api_url = data['api_url']
        if 'username' in data:
            blog.username = data['username']
        if 'api_token' in data:
            blog.api_token = data['api_token']
        if 'active' in data:
            blog.active = data['active']
        if 'approval_required' in data:
            blog.approval_required = data['approval_required']
        
        db.session.commit()
        
        # If blog was activated, sync categories
        if data.get('active', False) and not blog.active:
            sync_result = sync_blog_categories(blog_id)
            if sync_result['success'] and not AutomationRule.query.filter_by(blog_id=blog_id).first():
                create_default_automation_rule(blog_id)
        
        return jsonify({
            'success': True,
            'message': f'Blog {blog.name} został zaktualizowany'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas aktualizacji bloga: {str(e)}'
        }), 500


@multi_blog_bp.route('/api/blogs/<int:blog_id>/toggle', methods=['POST'])
def toggle_blog_status(blog_id):
    """Toggle blog active status"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        data = request.get_json()
        new_status = data.get('active', not blog.active)
        
        # Test connection if activating
        if new_status and not blog.active:
            test_result = test_wordpress_connection(blog.api_url, blog.username, blog.api_token)
            if not test_result['success']:
                return jsonify({
                    'success': False,
                    'message': f'Nie można aktywować - błąd połączenia: {test_result["message"]}'
                }), 400
        
        blog.active = new_status
        db.session.commit()
        
        # Update automation rules status
        rules = AutomationRule.query.filter_by(blog_id=blog_id).all()
        for rule in rules:
            rule.is_active = new_status
        db.session.commit()
        
        status_text = "aktywowany" if new_status else "dezaktywowany"
        return jsonify({
            'success': True,
            'message': f'Blog {blog.name} został {status_text}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas zmiany statusu bloga: {str(e)}'
        }), 500


@multi_blog_bp.route('/api/blogs/<int:blog_id>/sync-categories', methods=['POST'])
def sync_categories_endpoint(blog_id):
    """Sync blog categories with WordPress"""
    try:
        result = sync_blog_categories(blog_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas synchronizacji kategorii: {str(e)}'
        }), 500


def test_wordpress_connection(api_url, username, api_token):
    """Test WordPress API connection"""
    try:
        # Test with categories endpoint
        categories_url = f"{api_url.rstrip('/')}/categories"
        
        response = requests.get(
            categories_url,
            auth=HTTPBasicAuth(username, api_token),
            timeout=10,
            params={'per_page': 1}
        )
        
        if response.status_code == 200:
            return {'success': True, 'message': 'Połączenie udane'}
        elif response.status_code == 401:
            return {'success': False, 'message': 'Nieprawidłowe dane logowania'}
        elif response.status_code == 403:
            return {'success': False, 'message': 'Brak uprawnień do API'}
        else:
            return {'success': False, 'message': f'Błąd HTTP {response.status_code}'}
            
    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'Timeout połączenia'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': 'Nie można połączyć z serwerem'}
    except Exception as e:
        return {'success': False, 'message': f'Błąd: {str(e)}'}


def sync_blog_categories(blog_id):
    """Sync categories from WordPress API"""
    try:
        blog = Blog.query.get(blog_id)
        if not blog:
            return {'success': False, 'message': 'Blog nie został znaleziony'}
        
        categories_url = f"{blog.api_url.rstrip('/')}/categories"
        
        response = requests.get(
            categories_url,
            auth=HTTPBasicAuth(blog.username, blog.api_token),
            timeout=15,
            params={'per_page': 100}  # Get up to 100 categories
        )
        
        if response.status_code != 200:
            return {'success': False, 'message': f'Błąd API: {response.status_code}'}
        
        wp_categories = response.json()
        
        # Clear existing categories for this blog
        Category.query.filter_by(blog_id=blog_id).delete()
        
        # Add new categories
        categories_added = 0
        for wp_cat in wp_categories:
            category = Category(
                blog_id=blog_id,
                name=wp_cat['name'],
                wordpress_id=wp_cat['id'],
                parent_id=wp_cat.get('parent', None) if wp_cat.get('parent', 0) > 0 else None,
                description=wp_cat.get('description', '')
            )
            db.session.add(category)
            categories_added += 1
        
        db.session.commit()
        
        return {
            'success': True, 
            'message': f'Zsynchronizowano {categories_added} kategorii',
            'categories_count': categories_added
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Błąd synchronizacji: {str(e)}'}


def create_default_automation_rule(blog_id):
    """Create default automation rule for new blog"""
    try:
        blog = Blog.query.get(blog_id)
        if not blog:
            return False
        
        # Get blog categories
        categories = Category.query.filter_by(blog_id=blog_id).all()
        category_ids = [cat.wordpress_id for cat in categories if cat.wordpress_id]
        
        # Determine posts per day based on blog name
        posts_per_day = 2  # Default
        interval_hours = 4   # Default
        
        if 'kosmetyki' in blog.name.lower():
            posts_per_day = 3
            interval_hours = 3
        elif 'homos' in blog.name.lower():
            posts_per_day = 2
            interval_hours = 4
        elif 'mama' in blog.name.lower():
            posts_per_day = 4
            interval_hours = 2.5
        
        # Create automation rule
        rule = AutomationRule(
            blog_id=blog_id,
            name=f'Auto {blog.name}',
            description=f'Automatyczne generowanie artykułów dla {blog.name}',
            posts_per_day=posts_per_day,
            topic_categories=json.dumps(category_ids),
            is_active=True,
            publishing_time='09:00',
            days_of_week='0,1,2,3,4,5,6',  # Daily
            min_interval_hours=interval_hours,
            paragraph_count=4,
            use_paragraph_mode=True,
            content_tone='informative',
            min_word_count=800,
            max_word_count=1200,
            publish_immediately=True,
            apply_featured_image=True
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default automation rule: {e}")
        return False


# Register the blueprint with the app
app.register_blueprint(multi_blog_bp)