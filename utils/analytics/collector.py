import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

from models import Blog, ContentLog, ContentMetrics, PerformanceReport, AnalyticsConfig
from app import db
from utils.analytics.client import GA4Client

logger = logging.getLogger(__name__)

class AnalyticsCollector:
    """Collector for analytics data"""
    
    def __init__(self, ga4_client: Optional[GA4Client] = None):
        """
        Initialize analytics collector
        
        Args:
            ga4_client: Optional GA4 client instance
        """
        self.ga4_client = ga4_client or GA4Client()
    
    def sync_blog_metrics(self, blog_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Sync metrics for all posts in a blog
        
        Args:
            blog_id: Blog ID
            days: Number of days to look back
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get blog and analytics config
            blog = Blog.query.get(blog_id)
            if not blog:
                return {"error": f"Blog with ID {blog_id} not found"}
            
            config = AnalyticsConfig.query.filter_by(blog_id=blog_id).first()
            if not config or not config.active or not config.property_id:
                return {"error": f"Analytics not configured or inactive for blog {blog.name}"}
            
            # Get published posts
            posts = ContentLog.query.filter_by(
                blog_id=blog_id, 
                status="published"
            ).filter(
                ContentLog.published_at >= datetime.utcnow() - timedelta(days=days * 2)
            ).all()
            
            if not posts:
                return {"status": "no_posts", "message": f"No published posts found for blog {blog.name}"}
            
            # Set date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Sync metrics for each post
            results = {
                "total_posts": len(posts),
                "synced_posts": 0,
                "failed_posts": 0,
                "total_views": 0
            }
            
            for post in posts:
                if not post.post_id:
                    results["failed_posts"] += 1
                    continue
                
                # Get post URL from WordPress
                post_url = f"{blog.url.rstrip('/')}/?p={post.post_id}"
                
                # Get metrics for the post
                metrics = self.ga4_client.get_page_metrics(
                    property_id=config.property_id,
                    page_path=post_url,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if "error" in metrics:
                    results["failed_posts"] += 1
                    logger.error(f"Error getting metrics for post {post.title}: {metrics['error']}")
                    continue
                
                # Save or update metrics
                existing_metrics = ContentMetrics.query.filter_by(
                    blog_id=blog_id,
                    post_id=post.post_id
                ).first()
                
                if existing_metrics:
                    # Update existing metrics
                    existing_metrics.page_views = metrics["page_views"]
                    existing_metrics.unique_visitors = metrics["unique_visitors"]
                    existing_metrics.avg_time_on_page = metrics["avg_time_on_page"]
                    existing_metrics.bounce_rate = metrics["bounce_rate"]
                    existing_metrics.updated_at = datetime.utcnow()
                    existing_metrics.set_raw_data(metrics)
                else:
                    # Create new metrics
                    new_metrics = ContentMetrics(
                        blog_id=blog_id,
                        post_id=post.post_id,
                        title=post.title,
                        url=post_url,
                        page_views=metrics["page_views"],
                        unique_visitors=metrics["unique_visitors"],
                        avg_time_on_page=metrics["avg_time_on_page"],
                        bounce_rate=metrics["bounce_rate"],
                        updated_at=datetime.utcnow()
                    )
                    new_metrics.set_raw_data(metrics)
                    db.session.add(new_metrics)
                
                results["synced_posts"] += 1
                results["total_views"] += metrics["page_views"]
            
            # Update last sync time
            config.last_sync = datetime.utcnow()
            db.session.commit()
            
            return {
                "status": "success",
                "blog": blog.name,
                "synced_posts": results["synced_posts"],
                "failed_posts": results["failed_posts"],
                "total_views": results["total_views"]
            }
            
        except Exception as e:
            logger.error(f"Error syncing blog metrics: {str(e)}")
            db.session.rollback()
            return {"error": str(e)}
    
    def generate_performance_report(
        self,
        blog_id: int,
        report_type: str = "weekly",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        generate_insights: bool = True
    ) -> Union[PerformanceReport, Dict[str, str]]:
        """
        Generate performance report for a blog
        
        Args:
            blog_id: Blog ID
            report_type: Report type (daily, weekly, monthly, custom)
            start_date: Start date (required for custom reports)
            end_date: End date (required for custom reports)
            generate_insights: Whether to generate AI insights
            
        Returns:
            PerformanceReport instance or error dictionary
        """
        try:
            # Get blog
            blog = Blog.query.get(blog_id)
            if not blog:
                return {"error": f"Blog with ID {blog_id} not found"}
            
            # Set date range based on report type
            if not end_date:
                end_date = datetime.utcnow()
            
            if not start_date:
                if report_type == "daily":
                    start_date = end_date - timedelta(days=1)
                elif report_type == "weekly":
                    start_date = end_date - timedelta(days=7)
                elif report_type == "monthly":
                    start_date = end_date - timedelta(days=30)
                elif report_type == "quarterly":
                    start_date = end_date - timedelta(days=90)
                else:
                    return {"error": f"Invalid report type: {report_type}"}
            
            # Get content metrics for the date range
            metrics = ContentMetrics.query.filter(
                ContentMetrics.blog_id == blog_id,
                ContentMetrics.updated_at >= start_date,
                ContentMetrics.updated_at <= end_date
            ).all()
            
            if not metrics:
                return {"error": f"No metrics found for blog {blog.name} in the selected date range"}
            
            # Calculate aggregated metrics
            total_views = sum(m.page_views for m in metrics)
            total_visitors = sum(m.unique_visitors for m in metrics)
            
            # Calculate average bounce rate (weighted by views)
            total_weighted_bounce = sum(m.bounce_rate * m.page_views for m in metrics)
            avg_bounce_rate = total_weighted_bounce / total_views if total_views > 0 else 0
            
            # Get top posts
            top_posts = []
            for m in metrics:
                top_posts.append({
                    "post_id": m.post_id,
                    "title": m.title,
                    "url": m.url,
                    "views": m.page_views,
                    "visitors": m.unique_visitors,
                    "bounce_rate": m.bounce_rate
                })
            
            # Sort by views
            top_posts.sort(key=lambda x: x["views"], reverse=True)
            top_posts = top_posts[:10]  # Keep only top 10
            
            # Create report
            report = PerformanceReport(
                blog_id=blog_id,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                total_views=total_views,
                total_visitors=total_visitors,
                avg_bounce_rate=avg_bounce_rate
            )
            
            # Set top posts
            report.set_top_posts(top_posts)
            
            # Generate insights if requested
            if generate_insights:
                insights, recommendations = self._generate_ai_insights(metrics, blog, report_type)
                report.set_insights(insights)
                report.set_recommendations(recommendations)
            
            # Save report
            db.session.add(report)
            db.session.commit()
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            db.session.rollback()
            return {"error": str(e)}
    
    def _generate_ai_insights(
        self, 
        metrics: List[ContentMetrics],
        blog: Blog,
        report_type: str
    ) -> Tuple[List[str], List[str]]:
        """
        Generate AI insights and recommendations based on metrics
        
        Args:
            metrics: List of ContentMetrics
            blog: Blog instance
            report_type: Report type
            
        Returns:
            Tuple of (insights, recommendations)
        """
        # This is a placeholder for AI-generated insights
        # In a real implementation, this would call an AI service (OpenRouter, Claude, etc.)
        
        # For now, we'll return some basic insights based on the data
        insights = []
        recommendations = []
        
        # Calculate basic insights
        total_posts = len(metrics)
        total_views = sum(m.page_views for m in metrics)
        avg_views_per_post = total_views / total_posts if total_posts > 0 else 0
        
        # Sort posts by views
        sorted_posts = sorted(metrics, key=lambda m: m.page_views, reverse=True)
        
        # Get top and bottom performers
        top_performers = sorted_posts[:3]
        bottom_performers = sorted_posts[-3:] if len(sorted_posts) >= 3 else []
        
        # Basic insights
        insights.append(f"Total {total_posts} posts analyzed with {total_views} total views.")
        insights.append(f"Average views per post: {avg_views_per_post:.1f}")
        
        if top_performers:
            insights.append("Top performing content:")
            for i, post in enumerate(top_performers, 1):
                insights.append(f"  {i}. '{post.title}' with {post.page_views} views")
            
            # Look for patterns in top performers
            top_titles = [p.title.lower() for p in top_performers]
            
            # Check for common words in titles
            common_words = self._find_common_words(top_titles)
            if common_words:
                insights.append(f"Top posts often contain these words: {', '.join(common_words)}")
        
        # Basic recommendations
        if top_performers and bottom_performers:
            recommendations.append("Content strategy recommendations:")
            
            # Compare top and bottom performers
            if any(p.page_views > 0 for p in top_performers):
                recommendations.append("Create more content similar to your top performers.")
                
                # Recommend content calendar adjustments
                if report_type in ["weekly", "monthly"]:
                    recommendations.append("Consider increasing publishing frequency for content types that perform well.")
        
        # Add default recommendations if we don't have enough data
        if not recommendations:
            recommendations.append("Collect more data to generate specific content recommendations.")
            recommendations.append("Use AI-driven topic suggestions to optimize your content strategy.")
        
        return insights, recommendations
    
    def _find_common_words(self, titles: List[str]) -> List[str]:
        """
        Find common words in a list of titles
        
        Args:
            titles: List of titles
            
        Returns:
            List of common words
        """
        # Simple implementation to find common words
        common_words = []
        
        # Combine all words
        all_words = []
        for title in titles:
            words = [w.lower() for w in title.split() if len(w) > 3]
            all_words.extend(words)
        
        # Count occurrences
        word_counts = {}
        for word in all_words:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
        
        # Filter for words that appear in multiple titles
        for word, count in word_counts.items():
            if count > 1 and word not in ["this", "that", "with", "from", "your", "about"]:
                common_words.append(word)
        
        return common_words[:5]  # Return top 5 common words
    
    def schedule_content_based_on_performance(
        self,
        blog_id: int,
        days_ahead: int = 30,
        posts_per_day: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Schedule content based on performance data
        
        Args:
            blog_id: Blog ID
            days_ahead: Number of days to schedule ahead
            posts_per_day: Number of posts per day (if None, use blog setting)
            
        Returns:
            Dictionary with scheduling results
        """
        try:
            # Get blog
            blog = Blog.query.get(blog_id)
            if not blog:
                return {"error": f"Blog with ID {blog_id} not found"}
            
            # Get approved topics
            topics = ArticleTopic.query.filter_by(
                blog_id=blog_id,
                status="approved"
            ).order_by(ArticleTopic.score.desc()).all()
            
            if not topics:
                return {"error": f"No approved topics found for blog {blog.name}"}
            
            # Determine posts per day
            if posts_per_day is None:
                from config import Config
                posts_per_day = Config.ARTICLES_PER_DAY_PER_BLOG
            
            # Get existing scheduled content
            existing = ContentCalendar.query.filter_by(
                blog_id=blog_id,
                status="planned"
            ).filter(
                ContentCalendar.scheduled_date >= datetime.utcnow()
            ).all()
            
            # Find dates that already have content scheduled
            scheduled_dates = {}
            for entry in existing:
                date_key = entry.scheduled_date.strftime('%Y-%m-%d')
                if date_key in scheduled_dates:
                    scheduled_dates[date_key] += 1
                else:
                    scheduled_dates[date_key] = 1
            
            # Determine scheduling
            now = datetime.utcnow()
            scheduled_count = 0
            results = {
                "scheduled": [],
                "skipped_dates": [],
                "topics_used": 0
            }
            
            # Schedule for each day
            topic_index = 0
            for day in range(1, days_ahead + 1):
                target_date = now + timedelta(days=day)
                date_key = target_date.strftime('%Y-%m-%d')
                
                # Skip weekends if configured
                if target_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    results["skipped_dates"].append(date_key)
                    continue
                
                # Get existing count for this day
                existing_count = scheduled_dates.get(date_key, 0)
                
                # How many more posts do we need?
                needed_posts = posts_per_day - existing_count
                
                if needed_posts <= 0:
                    results["skipped_dates"].append(date_key)
                    continue
                
                # Schedule posts for this day
                from config import Config
                publishing_times = Config.PUBLISHING_TIMES
                time_index = existing_count
                
                for i in range(needed_posts):
                    # Check if we've used all topics
                    if topic_index >= len(topics):
                        break
                    
                    topic = topics[topic_index]
                    topic_index += 1
                    
                    # Determine time of day
                    if time_index < len(publishing_times):
                        time_str = publishing_times[time_index]
                        hour, minute = map(int, time_str.split(':'))
                        
                        scheduled_datetime = target_date.replace(
                            hour=hour, minute=minute, second=0, microsecond=0
                        )
                        
                        # Create calendar entry
                        entry = ContentCalendar(
                            blog_id=blog_id,
                            topic_id=topic.id,
                            title=topic.title,
                            scheduled_date=scheduled_datetime,
                            status="planned",
                            priority=min(5, max(1, int(topic.score * 5)))  # Convert score to 1-5 scale
                        )
                        
                        db.session.add(entry)
                        
                        # Update topic status
                        topic.status = "scheduled"
                        
                        # Record in results
                        results["scheduled"].append({
                            "date": scheduled_datetime.strftime('%Y-%m-%d %H:%M'),
                            "title": topic.title,
                            "priority": entry.priority
                        })
                        
                        scheduled_count += 1
                        time_index += 1
                    else:
                        # No more time slots for this day
                        break
            
            # Save changes
            db.session.commit()
            
            results["topics_used"] = topic_index
            return {
                "status": "success",
                "blog": blog.name,
                "total_scheduled": scheduled_count,
                "details": results
            }
            
        except Exception as e:
            logger.error(f"Error scheduling content: {str(e)}")
            db.session.rollback()
            return {"error": str(e)}