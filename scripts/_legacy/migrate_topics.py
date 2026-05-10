"""
Migration script to add description column to article_topic table
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add description column to article_topic table"""
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable is not set")
            sys.exit(1)
            
        # Create engine
        engine = create_engine(db_url)
        
        # Create connection
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name='article_topic' AND column_name='description')"
            ))
            column_exists = result.scalar()
            
            if column_exists:
                logger.info("Description column already exists in article_topic table")
                return
                
            # Add column
            conn.execute(text(
                "ALTER TABLE article_topic ADD COLUMN description TEXT"
            ))
            
            # Commit transaction
            conn.commit()
            
            logger.info("Successfully added description column to article_topic table")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()