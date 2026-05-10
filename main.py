"""
MasterContentAI - Application entry point.

This is the main module imported by gunicorn / Flask CLI.
All blueprint registration happens inside `routes.register_routes(app)`,
keeping a single source of truth for the app's URL map.
"""

import logging
import os

from app import app, db
from routes import register_routes  # noqa: F401 - registered via app.py
from utils.scheduler import start_scheduler
from utils.seo.analyzer import initialize_seo_module
from models import Blog  # noqa: F401 - imported to ensure model is loaded

# Logging is already configured in app.py — just get the logger here
logger = logging.getLogger(__name__)


def _auto_migrate_schema():
    """Apply lightweight schema patches that db.create_all() can't do.

    SQLAlchemy's create_all() never adds columns to existing tables, so
    when we rename or fix model attributes (like ScheduledSocialPost.content
    that used to be clobbered by a relationship of the same name) the
    physical column may be missing in legacy databases. We patch known
    cases here, idempotently.
    """
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)

    def _ensure_column(table_name: str, column_name: str, column_type: str):
        if not insp.has_table(table_name):
            return
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if column_name in cols:
            return
        with db.engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'))
        logger.info("Auto-migrated: ADDED %s.%s (%s)", table_name, column_name, column_type)

    # ScheduledSocialPost.content was historically shadowed by a relationship
    # of the same name, so the column was never created in legacy databases.
    _ensure_column("scheduled_social_post", "content", "TEXT")


def initialize_database():
    """Create database tables on first run + apply lightweight schema patches."""
    db.create_all()
    _auto_migrate_schema()
    if Blog.query.count() == 0:
        logger.info("No blogs found in database. Add them via the dashboard.")


# Bootstrap the application
with app.app_context():
    initialize_database()

    # Start the scheduler (manual content generation only - automatic disabled)
    try:
        start_scheduler()
    except Exception as exc:
        logger.error("Scheduler failed to start: %s", exc)

    # Initialize SEO module (Google Trends + SerpAPI)
    try:
        initialize_seo_module()
        logger.info("SEO module initialized")
    except Exception as exc:
        logger.error("Error initializing SEO module: %s", exc)

    logger.info("MasterContentAI application initialized")


if __name__ == "__main__":
    # Production should use gunicorn. Local dev: FLASK_DEBUG=1 enables debugger.
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info("Starting Flask dev server on %s:%s (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)
