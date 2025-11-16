# Blog Automation Agent

## Overview
This project is a comprehensive Flask-based blog automation system designed to manage the entire content lifecycle. It automates content creation from topic generation to publication and social media promotion. The system integrates with various AI models via OpenRouter API, manages publishing to WordPress sites, and handles social media distribution, aiming to provide a fully autonomous content generation and marketing solution.

**Current Configuration (Updated November 16, 2025):**
- **Daily Article Production**: 9 articles total (3 per blog)
  - MAMATESTUJE.COM: 3 articles/day
  - ZNANEKOSMETYKI.PL: 3 articles/day
  - HOMOSONLY.PL: 3 articles/day
- **Publication Schedule**: Polish business hours (07:00, 08:00, 09:00 AM UTC+1)
- **AI Model**: DeepSeek V3 0324 (deepseek/deepseek-chat-v3-0324:free) - free model for all content generation

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Technical Stack
- **Backend**: Flask (Python) with SQLAlchemy ORM, SQLite (PostgreSQL for production).
- **Frontend**: Jinja2 templates, Bootstrap 5.3.2, custom CSS (Consist UI color scheme), Vanilla JS, Font Awesome 6.4.0.
- **AI Integration**: OpenRouter API with DeepSeek V3 0324 (free model) for all content generation.
- **CMS Integration**: WordPress REST API.
- **Task Scheduling**: APScheduler.

### Core Features
- **Content Generation Engine**: AI-powered topic suggestion, article writing (paragraph-based, configurable length), SEO optimization (meta descriptions, keywords), and automatic image sourcing (Unsplash, Google Images, Pexels). Enhanced with sentence completion validation ensuring all articles end with complete sentences and proper HTML tag closure.
- **Publishing System**: WordPress integration with scheduling, draft management, and automatic category/tag assignment. Features include 4-page A4 article generation (minimum 1200 words), exactly 12 SEO tags per article, and automated featured image integration.
- **Social Media Automation**: Multi-platform support (Facebook, Twitter, LinkedIn, Instagram, TikTok) for auto-posting, content adaptation, and engagement tracking.
- **SEO and Analytics**: Google Trends for topic discovery, SerpAPI for keyword research, content metrics tracking, and optimization suggestions.
- **Multi-Blog Management**: Supports simultaneous content generation and publishing across multiple WordPress blogs with independent configurations and author rotation.
- **Workflow Engine**: Orchestrates the entire content lifecycle, including topic management, article generation, image integration, validation, and publication with retry mechanisms and error handling.
- **Category Rotation System**: Ensures diversity in batch generation - each consecutive article uses a different category, cycling through all available categories before repeating.
- **Author Rotation System**: Automatically rotates through WordPress authors for batch generation. Fetches real authors from WordPress API and assigns them cyclically to ensure balanced content distribution across the editorial team.

### System Design Choices
- **Database Schema**: Includes tables for Blog configurations, ContentLog, ArticleTopic, Category/Tag, SocialAccount, AutomationRule, and Newsletter.
- **Deployment**: Development uses SQLite and debug mode; production uses PostgreSQL, gunicorn, and environment variables for sensitive data.
- **Scalability**: Designed with PostgreSQL for production, session-based caching, API rate limiting, and robust error handling.
- **Security**: Environment variable management for API keys, secure session handling, SQL injection protection via SQLAlchemy, and input validation.

## External Dependencies

### AI Services
- **OpenRouter API**: Primary AI service using DeepSeek V3 0324 (free model) for all content generation, topic generation, and social media content.
- **Anthropic API**: Direct Claude access (fallback).
- **OpenAI API**: Direct GPT access (fallback).

### Content Services
- **WordPress REST API**: For blog content management.
- **Unsplash API**: For high-quality images.
- **Google Custom Search API**: For image search functionality.
- **Pexels API**: For additional image sourcing.
- **SerpAPI**: For SEO analysis and keyword research.

### Social Media APIs
- **Facebook Graph API**: For Facebook posting.
- **Twitter API**: For Twitter automation.
- **LinkedIn API**: For professional network posting.
- **Buffer API**: (Optional) for social media scheduling.

### Analytics and SEO
- **Google Analytics 4**: For traffic and engagement tracking.
- **Google Trends**: For trend analysis in topic generation.
- **SerpAPI**: For SERP analysis and keyword competition.