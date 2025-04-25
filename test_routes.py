"""
Test script to list all registered routes in the Flask app
"""
from app import app
from routes import register_routes

# Register all routes
register_routes(app)

# Print all registered routes
print("All registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule} -> {rule.endpoint}")

# Print all registered blueprints
print("\nAll registered blueprints:")
for blueprint_name in app.blueprints:
    print(blueprint_name)