from models.user import db, User
from models.admin import Admin
from server import create_app
import os

app = create_app()
with app.app_context():
    # Ensure tables exist
    db.create_all()
    
    # Move admin@example.com from User to Admin
    u = User.query.filter_by(email='admin@example.com').first()
    if u:
        print(f"Deleting user {u.email} from User table")
        db.session.delete(u)
    
    # Check if admin exists in Admin table
    a = Admin.query.filter_by(email='admin@example.com').first()
    if not a:
        print("Creating admin@example.com in Admin table")
        new_admin = Admin(
            name='Administrator',
            number='1234567890',
            email='admin@example.com',
            password='admin123'
        )
        db.session.add(new_admin)
    else:
        print("Admin admin@example.com already exists in Admin table")
        # Update password just in case
        a.set_password('admin123')
        
    db.session.commit()
    print("Migration finished successfully")
