"""
Author Rotation System for Multi-Blog Content Publishing

Implements rotational author assignment based on daily article quotas:
- 4 artykuły dziennie = 4 autorów, po 1 artykule każdy
- 3 artykuły dziennie = 3 autorów, po 1 artykule każdy  
- 2 artykuły dziennie = 2 autorów, po 1 artykule każdy
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app import db
from models import Blog, ContentLog, AutomationRule
import requests
import base64

logger = logging.getLogger(__name__)

class AuthorRotationManager:
    """Manages rotational author assignment for multi-blog publishing"""
    
    def __init__(self):
        # Real WordPress author IDs (will be updated from WordPress API)
        self.blog_authors = {
            'MAMATESTUJE.COM': [],  # Will be populated from WordPress
            'ZNANEKOSMETYKI.PL': [], # Will be populated from WordPress  
            'HOMOSONLY.PL': []      # Will be populated from WordPress
        }
        self._populate_real_authors()
    
    def get_next_author_for_blog(self, blog_id: int, daily_quota: int) -> Optional[Dict]:
        """
        Returns next author in rotation based on daily quota
        
        Args:
            blog_id: Blog database ID
            daily_quota: Number of articles per day (2, 3, or 4)
            
        Returns:
            Dict with author info or None if no authors available
        """
        try:
            # Get blog info
            blog = Blog.query.get(blog_id)
            if not blog:
                logger.error(f"Blog with ID {blog_id} not found")
                return None
            
            blog_name = blog.name
            if blog_name not in self.blog_authors:
                logger.warning(f"No authors configured for blog {blog_name}")
                return None
            
            available_authors = self.blog_authors[blog_name]
            
            # Limit authors based on daily quota
            quota_authors = available_authors[:daily_quota]
            
            # Get today's published articles for this blog
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            published_today = ContentLog.query.filter(
                ContentLog.blog_id == blog_id,
                ContentLog.published_at >= today_start,
                ContentLog.published_at <= today_end,
                ContentLog.status == 'published'
            ).all()
            
            # Count articles by author today
            author_counts = {}
            for article in published_today:
                if hasattr(article, 'author_id') and article.author_id:
                    author_counts[article.author_id] = author_counts.get(article.author_id, 0) + 1
            
            # Find author with least articles today
            for author in quota_authors:
                author_id = author['id']
                current_count = author_counts.get(author_id, 0)
                
                # If this author hasn't published today, use them
                if current_count == 0:
                    logger.info(f"Selected author {author['name']} (ID: {author_id}) for blog {blog_name}")
                    return author
            
            # If all authors have published, cycle through them
            next_author_index = len(published_today) % len(quota_authors)
            selected_author = quota_authors[next_author_index]
            
            logger.info(f"Cycling to author {selected_author['name']} (ID: {selected_author['id']}) for blog {blog_name}")
            return selected_author
            
        except Exception as e:
            logger.error(f"Error getting next author for blog {blog_id}: {str(e)}")
            return None
    
    def get_author_distribution_for_blog(self, blog_id: int, days: int = 7) -> Dict:
        """
        Returns author distribution statistics for a blog over specified days
        
        Args:
            blog_id: Blog database ID
            days: Number of days to analyze (default 7)
            
        Returns:
            Dict with author statistics
        """
        try:
            blog = Blog.query.get(blog_id)
            if not blog:
                return {'error': f'Blog {blog_id} not found'}
            
            # Get articles from last N days
            start_date = datetime.utcnow() - timedelta(days=days)
            
            articles = ContentLog.query.filter(
                ContentLog.blog_id == blog_id,
                ContentLog.published_at >= start_date,
                ContentLog.status == 'published'
            ).all()
            
            # Count by author
            author_stats = {}
            total_articles = len(articles)
            
            for article in articles:
                if hasattr(article, 'author_id') and article.author_id:
                    author_id = article.author_id
                    if author_id not in author_stats:
                        author_stats[author_id] = {
                            'count': 0,
                            'percentage': 0,
                            'name': f'Author_{author_id}'
                        }
                    author_stats[author_id]['count'] += 1
            
            # Calculate percentages
            for author_id in author_stats:
                count = author_stats[author_id]['count']
                author_stats[author_id]['percentage'] = round((count / total_articles) * 100, 1) if total_articles > 0 else 0
            
            return {
                'blog_name': blog.name,
                'total_articles': total_articles,
                'days_analyzed': days,
                'author_distribution': author_stats,
                'balanced': self._is_distribution_balanced(author_stats)
            }
            
        except Exception as e:
            logger.error(f"Error getting author distribution for blog {blog_id}: {str(e)}")
            return {'error': str(e)}
    
    def _is_distribution_balanced(self, author_stats: Dict) -> bool:
        """Check if author distribution is reasonably balanced (within 20% variance)"""
        if not author_stats:
            return True
        
        percentages = [stats['percentage'] for stats in author_stats.values()]
        if not percentages:
            return True
        
        avg_percentage = sum(percentages) / len(percentages)
        max_variance = max(abs(p - avg_percentage) for p in percentages)
        
        return max_variance <= 20  # 20% tolerance
    
    def get_daily_author_schedule(self, blog_id: int) -> List[Dict]:
        """
        Returns planned author schedule for today based on automation rules
        
        Args:
            blog_id: Blog database ID
            
        Returns:
            List of scheduled authors for today
        """
        try:
            # Get automation rule for this blog
            rule = AutomationRule.query.filter_by(
                blog_id=blog_id,
                is_active=True
            ).first()
            
            if not rule:
                return []
            
            # Determine daily quota from automation rule
            daily_quota = self._extract_daily_quota_from_rule(rule)
            
            # Get authors for this quota
            blog = Blog.query.get(blog_id)
            if not blog or blog.name not in self.blog_authors:
                return []
            
            available_authors = self.blog_authors[blog.name][:daily_quota]
            
            # Create schedule with different categories for each author
            schedule = []
            categories = self._get_diverse_categories_for_blog(blog.name, daily_quota)
            
            for i, author in enumerate(available_authors):
                schedule.append({
                    'author_id': author['id'],
                    'author_name': author['name'],
                    'category': categories[i] if i < len(categories) else 'Ogólne',
                    'order': i + 1
                })
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error getting daily author schedule for blog {blog_id}: {str(e)}")
            return []
    
    def _extract_daily_quota_from_rule(self, rule: AutomationRule) -> int:
        """Extract daily article quota from automation rule configuration"""
        # Use posts_per_day field directly from automation rule
        if hasattr(rule, 'posts_per_day') and rule.posts_per_day:
            return int(rule.posts_per_day)
        
        # Fallback to minimum interval calculation
        if hasattr(rule, 'min_interval_hours') and rule.min_interval_hours:
            hours_per_day = 24
            quota = hours_per_day // rule.min_interval_hours
            return max(1, quota)  # At least 1 article per day
        
        return 2  # Default fallback
    
    def _get_diverse_categories_for_blog(self, blog_name: str, quota: int) -> List[str]:
        """Get diverse categories for articles to avoid overlap"""
        category_pools = {
            'MAMATESTUJE.COM': [
                'Planowanie ciąży',
                'Zdrowie w ciąży', 
                'Produkty dla dzieci',
                'Rozwój dziecka',
                'Żywienie dzieci',
                'Bezpieczeństwo dziecka'
            ],
            'ZNANEKOSMETYKI.PL': [
                'Pielęgnacja twarzy',
                'Makijaż',
                'Pielęgnacja włosów',
                'Perfumy',
                'Kosmetyki naturalne'
            ],
            'HOMOSONLY.PL': [
                'Lifestyle',
                'Moda męska',
                'Zdrowie mężczyzn',
                'Relacje'
            ]
        }
        
        pool = category_pools.get(blog_name, ['Ogólne'])
        
        # Return as many unique categories as quota requires
        return pool[:quota] if len(pool) >= quota else pool * ((quota // len(pool)) + 1)[:quota]
    
    def _populate_real_authors(self):
        """Populate real WordPress author IDs from WordPress API"""
        try:
            from app import app, db
            
            with app.app_context():
                blogs_config = [
                    {'name': 'MAMATESTUJE.COM', 'username': 'TomaszKotlinski', 'token': 'xylc IFTY xwwr QTQN suAM N5X6'},
                    {'name': 'ZNANEKOSMETYKI.PL', 'username': 'admin', 'token': 'HQFQ zPo1 E4pj wCp4 sLhu NCR3'},
                    {'name': 'HOMOSONLY.PL', 'username': 'admin', 'token': 'DmDc pWRg upV6 vjMM fbLm OAHU'}
                ]
                
                for blog_config in blogs_config:
                    blog = Blog.query.filter_by(name=blog_config['name']).first()
                    if not blog:
                        continue
                    
                    try:
                        # Get WordPress users
                        api_url = f'{blog.url}/wp-json/wp/v2/users'
                        username = blog_config['username']
                        user_token = blog_config['token']
                        credentials = f'{username}:{user_token}'
                        token = base64.b64encode(credentials.encode()).decode('utf-8')
                        headers = {
                            'Authorization': f'Basic {token}',
                            'Content-Type': 'application/json'
                        }
                        
                        response = requests.get(api_url, headers=headers, timeout=30)
                        
                        if response.status_code == 200:
                            users = response.json()
                            blog_authors = []
                            
                            for user in users:
                                user_id = user.get('id')
                                user_name = user.get('name') or user.get('slug') or f'User_{user_id}'
                                blog_authors.append({
                                    'id': user_id,
                                    'name': user_name,
                                    'slug': user.get('slug'),
                                    'weight': 1
                                })
                            
                            self.blog_authors[blog_config['name']] = blog_authors
                            logger.info(f"Loaded {len(blog_authors)} authors for {blog_config['name']}")
                            
                    except Exception as e:
                        logger.error(f"Error loading authors for {blog_config['name']}: {str(e)}")
                        # Fallback to default authors if API fails
                        if blog_config['name'] == 'MAMATESTUJE.COM':
                            self.blog_authors[blog_config['name']] = [{'id': 2, 'name': 'TomaszKotlinski', 'weight': 1}]
                        elif blog_config['name'] == 'ZNANEKOSMETYKI.PL':
                            self.blog_authors[blog_config['name']] = [{'id': 1, 'name': 'admin', 'weight': 1}]  
                        elif blog_config['name'] == 'HOMOSONLY.PL':
                            self.blog_authors[blog_config['name']] = [{'id': 1, 'name': 'admin', 'weight': 1}]
                            
        except Exception as e:
            logger.error(f"Error in _populate_real_authors: {str(e)}")
    
    def get_rotational_author_by_day_and_index(self, blog_name: str, article_index: int) -> Optional[Dict]:
        """
        Get rotational author based on day and article index (following user specification)
        
        Args:
            blog_name: Name of the blog
            article_index: Index of article for today (0, 1, 2, etc.)
            
        Returns:
            Dict with author info or None
        """
        try:
            import datetime
            
            if blog_name not in self.blog_authors:
                logger.error(f"Blog {blog_name} not found in authors")
                return None
                
            authors = self.blog_authors[blog_name]
            if not authors:
                logger.error(f"No authors found for blog {blog_name}")
                return None
            
            # Calculate rotational author based on day + article index
            day_index = datetime.date.today().toordinal()  # Unique day number
            author_index = (day_index + article_index) % len(authors)
            
            selected_author = authors[author_index]
            logger.info(f"Rotational author for {blog_name} article {article_index}: {selected_author['name']}")
            
            return selected_author
            
        except Exception as e:
            logger.error(f"Error getting rotational author: {str(e)}")
            return None

# Global instance
author_rotation_manager = AuthorRotationManager()