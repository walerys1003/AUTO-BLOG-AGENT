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

## Recent Changes

### June 29, 2025 - WordPress Publication Metadata Enhancement
- ✅ **Identified Missing Metadata Issue**: Published articles lacked proper categories, tags, and featured images
- ✅ **Enhanced Workflow Engine**: Added comprehensive metadata handling to WordPress publishing
- ✅ **Category Assignment System**: Implemented automatic category ID detection and assignment
- ✅ **Tag Generation System**: Added intelligent tag creation based on article categories
- ✅ **Featured Image Integration**: Built automatic image upload and assignment workflow
- ✅ **Topic Management Improvement**: Added new Polish topic generation for continued automation
- ❌ **WordPress API Permissions**: Encountered authorization issues with metadata updates on existing posts
- → **Next Deployment**: New articles will include proper categories, tags, and featured images automatically

**Publication Enhancement Status**: System now ready for complete article metadata integration
- Categories automatically assigned based on article topic (e.g., "Planowanie ciąży" → ID: 3)
- Tags generated contextually (planowanie ciąży, płodność, zdrowie, rodzina, etc.)
- Featured images uploaded and assigned to posts during publication
- Comprehensive logging for metadata assignment verification
- New Polish topics generated and approved for continued automation

### June 29, 2025 - Polish Language Content Implementation
- ✅ **Complete Polish Localization**: All content generation now produces Polish articles and topics
- ✅ **AI Topic Generator Fixed**: Updated to handle "tematy" key in Polish AI responses
- ✅ **Full Category Integration**: Added all 64 MamaTestuje.com categories from WordPress API
- ✅ **Polish Topics Database**: Generated authentic Polish topics for key categories (Planowanie ciąży, Zdrowie w ciąży, etc.)
- ✅ **Workflow Language Fix**: Fixed workflow engine to use correct topic fields (title vs topic)
- ✅ **Database Integration**: Resolved schema issues with approved_by field and topic storage

**Language Status**: MASTER AGENT AI now generates 100% Polish content
- Topic generation uses Polish prompts and expects Polish responses
- Article generation produces Polish titles, content, and meta descriptions
- All fallback content is in Polish language
- WordPress categories match authentic MamaTestuje.com taxonomy

### June 28, 2025 - Automatic Image Integration with Content Creator
- ✅ **Auto Image Finding**: Integrated automatic image search with content generation workflow
- ✅ **Google Images API Fix**: Fixed critical parameter bug (LARGE vs large) in Google Custom Search API
- ✅ **UI Integration**: Added "Automatycznie wyszukaj obrazy" checkbox to content creation forms
- ✅ **Image Library**: Automatic saving of found images to database image_library table
- ✅ **Featured Image**: First found image automatically set as article featured image
- ✅ **End-to-End Testing**: Confirmed full workflow from AI content generation to automatic image finding

### June 28, 2025 - Complete Automation System Implementation
- ✅ **Workflow Engine**: Implemented central automation orchestrator (utils/automation/workflow_engine.py)
- ✅ **Topic Manager**: Built topic lifecycle management with bulk approval (utils/automation/topic_manager.py)  
- ✅ **Automation Scheduler**: Created automated execution scheduler running every 15 minutes (utils/automation/scheduler.py)
- ✅ **Dashboard Integration**: Added automation management interface (/automation/dashboard)
- ✅ **Database Extensions**: Extended models with workflow tracking fields and status management
- ✅ **API Endpoints**: Implemented REST API for automation control (/automation/api/*)

### June 28, 2025 - Advanced Publication Scheduler with Author Rotation
- ✅ **Real WordPress Categories**: Updated scheduler to use authentic MamaTestuje.com categories (85 categories from WordPress API)
- ✅ **Product-Review Content**: Transformed from generic parenting topics to product-focused review articles
- ✅ **Author Management System**: Integrated 4 real journalists from WordPress with intelligent rotation
- ✅ **Specialization Matching**: Authors automatically assigned based on category expertise
- ✅ **30-Day Scheduling**: 100 articles with balanced category distribution and author rotation

**Author Rotation System**:
- **Tomasz Kotliński** (ID: 2): Administrator, 7373 existing posts, 25% weight
- **Gabriela Bielec** (ID: 5): Child products specialist, 25% weight  
- **Helena Rybikowska** (ID: 4): Child health expert, 25% weight
- **Zofia Chryplewicz** (ID: 3): Cosmetics specialist, 25% weight

**System Status**: MASTER AGENT AI is now fully autonomous and operational
- 2 active automation rules running
- 15 approved topics ready for use  
- 0 failed rules
- Scheduler running successfully with 8 scheduled jobs
- Advanced publication scheduler with author rotation ready

**Capabilities Achieved**:
- Autonomous topic generation from AI for blog categories
- Bulk topic approval and management system
- Complete article generation pipeline (topic → content → images → WordPress → social media)
- Automated scheduling and execution of content workflows
- Real-time monitoring and error tracking
- Manual override and testing capabilities
- Intelligent author assignment based on specializations
- Product-review focused content generation for MamaTestuje.com

### Initial Setup
- June 28, 2025. Project foundation established