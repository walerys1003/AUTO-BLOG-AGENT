"""
Script to update the database schema
"""
from app import app, db
import models

def add_missing_columns():
    """
    Add missing columns to the AutomationRule table
    """
    from sqlalchemy import text
    
    with app.app_context():
        # Check if content_length column exists
        with db.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='automation_rule' AND column_name='content_length'"
            ))
            if not list(result):
                print("Adding content_length column to automation_rule table")
                conn.execute(text(
                    "ALTER TABLE automation_rule "
                    "ADD COLUMN content_length VARCHAR(20) DEFAULT 'medium'"
                ))
                conn.commit()
                print("Column added successfully")
            else:
                print("content_length column already exists")

        # Always ensure the paragraph-related columns exist
        with db.engine.connect() as conn:
            # Check and add paragraph_count if needed
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='automation_rule' AND column_name='paragraph_count'"
            ))
            if not list(result):
                print("Adding paragraph_count column to automation_rule table")
                conn.execute(text(
                    "ALTER TABLE automation_rule "
                    "ADD COLUMN paragraph_count INTEGER DEFAULT 4"
                ))
                conn.commit()
                print("Column added successfully")
            else:
                print("paragraph_count column already exists")
                
            # Check and add use_paragraph_mode if needed
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='automation_rule' AND column_name='use_paragraph_mode'"
            ))
            if not list(result):
                print("Adding use_paragraph_mode column to automation_rule table")
                conn.execute(text(
                    "ALTER TABLE automation_rule "
                    "ADD COLUMN use_paragraph_mode BOOLEAN DEFAULT false"
                ))
                conn.commit()
                print("Column added successfully")
            else:
                print("use_paragraph_mode column already exists")

if __name__ == "__main__":
    add_missing_columns()
    print("Database update completed")