from models.user import db, User
from models.admin import Admin
from server import create_app

app = create_app()
with app.app_context():
    # Student
    if not User.query.filter_by(email='student@example.com').first():
        s = User(name='Student', email='student@example.com', password='student123', role='student')
        db.session.add(s)
    
    # Faculty
    if not User.query.filter_by(email='faculty@example.com').first():
        f = User(name='Faculty', email='faculty@example.com', password='faculty123', role='faculty')
        db.session.add(f)
        
    db.session.commit()
    print("Seed complete")
