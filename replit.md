# Blog Automation Agent - System Architecture

## Overview

This is a comprehensive Flask-based blog automation system that handles the entire content lifecycle - from topic generation to publication and social media promotion. The system integrates with AI models (Claude Sonnet 3.5, GPT-4) through OpenRouter API to generate content automatically, manages WordPress publishing, and handles social media distribution.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python) with SQLAlchemy ORM
- **Database**: SQLite (configurable to PostgreSQL via DATABASE_URL)
- **AI Integration**: OpenRouter API for Claude Sonnet 3.5 and GPT-4 models
- **Content Management**: WordPress REST API integration
- **Task Scheduling**: APScheduler for automated content generation

### Frontend Architecture
- **Templates**: Jinja2 templating with Bootstrap 5.3.2
- **Styling**: Custom CSS with Consist UI color scheme
- **JavaScript**: Vanilla JS for dynamic interactions
- **Icons**: Font Awesome 6.4.0

### Database Schema
- **Blog**: WordPress blog configurations and API credentials
- **ContentLog**: Generated articles with metadata and publishing status
- **ArticleTopic**: AI-generated topic suggestions with approval workflow
- **Category/Tag**: WordPress taxonomy management
- **SocialAccount**: Social media platform integrations
- **AutomationRule**: Content generation automation settings
- **Newsletter**: Email newsletter management

## Key Components

### 1. Content Generation Engine
- **Topic Generation**: AI-powered topic suggestion based on SEO trends
- **Article Writing**: Paragraph-based content generation with configurable length
- **SEO Optimization**: Meta descriptions, keywords, and optimization analysis
- **Image Integration**: Automatic image sourcing from Unsplash and Google Images

### 2. Publishing System
- **WordPress Integration**: REST API-based content publishing
- **Scheduling**: Automated publishing with configurable timing
- **Content Management**: Draft management and publishing workflow
- **Category Management**: Automatic categorization and tagging

### 3. Social Media Automation
- **Multi-platform Support**: Facebook, Twitter, LinkedIn, Instagram, TikTok
- **Auto-posting**: Automatic social media post generation from articles
- **Content Adaptation**: Platform-specific content formatting
- **Engagement Tracking**: Social media performance metrics

### 4. SEO and Analytics
- **Trend Analysis**: Google Trends integration for topic discovery
- **SERP Analysis**: SerpAPI for keyword research and competition analysis
- **Performance Tracking**: Content metrics and analytics collection
- **Optimization Tools**: Content analysis and improvement suggestions

## Data Flow

1. **Topic Generation**: AI analyzes trends and generates article topics
2. **Topic Approval**: Manual or automated topic approval workflow
3. **Content Creation**: AI generates full articles based on approved topics
4. **Image Sourcing**: Automatic image selection and embedding
5. **SEO Processing**: Meta tag generation and optimization
6. **Publishing**: WordPress publication with scheduling
7. **Social Distribution**: Automated social media posting
8. **Analytics Collection**: Performance tracking and reporting

## External Dependencies

### AI Services
- **OpenRouter API**: Primary AI model access (Claude Sonnet 3.5, GPT-4)
- **Anthropic API**: Direct Claude API access (fallback)
- **OpenAI API**: Direct GPT access (fallback)

### Content Services
- **WordPress REST API**: Blog content management
- **Unsplash API**: High-quality image sourcing
- **Google Custom Search API**: Image search functionality
- **SerpAPI**: SEO analysis and keyword research

### Social Media APIs
- **Facebook Graph API**: Facebook posting
- **Twitter API**: Tweet automation
- **LinkedIn API**: Professional network posting
- **Buffer API**: Social media scheduling (optional)

### Analytics and SEO
- **Google Analytics 4**: Traffic and engagement tracking
- **Google Trends**: Trend analysis for topic generation
- **SerpAPI**: SERP analysis and keyword competition

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database, debug mode enabled
- **Production**: PostgreSQL database, gunicorn WSGI server
- **Environment Variables**: API keys, database URLs, feature flags

### Scaling Considerations
- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: Session-based caching for temporary data
- **Rate Limiting**: Built-in API rate limiting for external services
- **Error Handling**: Comprehensive error logging and recovery

### Security
- **API Key Management**: Environment variable based configuration
- **Session Security**: Configurable session secrets
- **Database Security**: SQL injection protection via SQLAlchemy ORM
- **Input Validation**: Form validation and sanitization

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- June 28, 2025. Initial setup