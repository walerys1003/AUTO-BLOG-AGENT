# Blog Automation Agent

## Overview
This project is a comprehensive Flask-based blog automation system designed to manage the entire content lifecycle. It automates content creation from topic generation to publication and social media promotion. The system integrates with various AI models via OpenRouter API, manages publishing to WordPress sites, and handles social media distribution, aiming to provide a fully autonomous content generation and marketing solution.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Technical Stack
- **Backend**: Flask (Python) with SQLAlchemy ORM, SQLite (PostgreSQL for production).
- **Frontend**: Jinja2 templates, Bootstrap 5.3.2, custom CSS (Consist UI color scheme), Vanilla JS, Font Awesome 6.4.0.
- **AI Integration**: OpenRouter API for Claude Sonnet 3.5 and GPT-4.
- **CMS Integration**: WordPress REST API.
- **Task Scheduling**: APScheduler.

### Core Features
- **Content Generation Engine**: AI-powered topic suggestion, article writing (paragraph-based, configurable length), SEO optimization (meta descriptions, keywords), and automatic image sourcing (Unsplash, Google Images, Pexels).
- **Publishing System**: WordPress integration with scheduling, draft management, and automatic category/tag assignment. Features include 4-page A4 article generation (minimum 1200 words), exactly 12 SEO tags per article, and automated featured image integration.
- **Social Media Automation**: Multi-platform support (Facebook, Twitter, LinkedIn, Instagram, TikTok) for auto-posting, content adaptation, and engagement tracking.
- **SEO and Analytics**: Google Trends for topic discovery, SerpAPI for keyword research, content metrics tracking, and optimization suggestions.
- **Multi-Blog Management**: Supports simultaneous content generation and publishing across multiple WordPress blogs with independent configurations and author rotation.
- **Workflow Engine**: Orchestrates the entire content lifecycle, including topic management, article generation, image integration, validation, and publication with retry mechanisms and error handling.
- **Author Rotation System**: Manages real WordPress authors, rotating them for content assignments based on categories and specializations.

### System Design Choices
- **Database Schema**: Includes tables for Blog configurations, ContentLog, ArticleTopic, Category/Tag, SocialAccount, AutomationRule, and Newsletter.
- **Deployment**: Development uses SQLite and debug mode; production uses PostgreSQL, gunicorn, and environment variables for sensitive data.
- **Scalability**: Designed with PostgreSQL for production, session-based caching, API rate limiting, and robust error handling.
- **Security**: Environment variable management for API keys, secure session handling, SQL injection protection via SQLAlchemy, and input validation.

## External Dependencies

### AI Services
- **OpenRouter API**: For Claude Sonnet 3.5, GPT-4.
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