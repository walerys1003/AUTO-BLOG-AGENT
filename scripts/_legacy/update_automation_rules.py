"""
Script to update the automation_rule table with new columns
"""
import logging
from app import app, db
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_columns_to_automation_rule():
    """Add new columns to the automation_rule table"""
    try:
        with app.app_context():
            # Check if the columns already exist
            result = db.session.execute(text("SELECT * FROM information_schema.columns WHERE table_name='automation_rule' AND column_name='publishing_time'"))
            publishing_time_exists = result.rowcount > 0

            result = db.session.execute(text("SELECT * FROM information_schema.columns WHERE table_name='automation_rule' AND column_name='topic_min_score'"))
            topic_min_score_exists = result.rowcount > 0

            result = db.session.execute(text("SELECT * FROM information_schema.columns WHERE table_name='automation_rule' AND column_name='auto_enable_topics'"))
            auto_enable_topics_exists = result.rowcount > 0

            result = db.session.execute(text("SELECT * FROM information_schema.columns WHERE table_name='automation_rule' AND column_name='auto_promote_content'"))
            auto_promote_content_exists = result.rowcount > 0

            # Add the missing columns if they don't exist
            if not publishing_time_exists:
                logger.info("Adding 'publishing_time' column to automation_rule table")
                db.session.execute(text("ALTER TABLE automation_rule ADD COLUMN publishing_time VARCHAR(5) DEFAULT '12:00'"))
            else:
                logger.info("Column 'publishing_time' already exists in automation_rule table")

            if not topic_min_score_exists:
                logger.info("Adding 'topic_min_score' column to automation_rule table")
                db.session.execute(text("ALTER TABLE automation_rule ADD COLUMN topic_min_score FLOAT DEFAULT 0.7"))
            else:
                logger.info("Column 'topic_min_score' already exists in automation_rule table")

            if not auto_enable_topics_exists:
                logger.info("Adding 'auto_enable_topics' column to automation_rule table")
                db.session.execute(text("ALTER TABLE automation_rule ADD COLUMN auto_enable_topics BOOLEAN DEFAULT TRUE"))
            else:
                logger.info("Column 'auto_enable_topics' already exists in automation_rule table")

            if not auto_promote_content_exists:
                logger.info("Adding 'auto_promote_content' column to automation_rule table")
                db.session.execute(text("ALTER TABLE automation_rule ADD COLUMN auto_promote_content BOOLEAN DEFAULT FALSE"))
            else:
                logger.info("Column 'auto_promote_content' already exists in automation_rule table")

            db.session.commit()
            logger.info("Successfully updated automation_rule table schema")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating automation_rule table schema: {str(e)}")
        raise

if __name__ == "__main__":
    add_columns_to_automation_rule()
    print("Schema update completed successfully!")