"""
Reset Database - Drop all tables and recreate with new schema
"""
import os
from server import create_app
from models.user import db

# Delete old database
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Deleted old database: {db_path}")

# Create app and recreate tables
app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully with new schema!")
    print("\nNow run:")
    print("  python migrate_admin.py  (to create admin account)")
    print("  python seed_users.py     (to create test users)")
