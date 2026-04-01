"""
Database Initialization Script for HostelHub
Run this script to create all tables and add sample admin user.
Usage: python init_db.py
"""

from app import create_app
from models import db, User, Room

def init_database():
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if admin exists
        admin = User.query.filter_by(email='admin@hostelhub.com').first()
        if not admin:
            # Create default admin user
            admin = User(
                name='Admin User',
                email='admin@hostelhub.com',
                role='admin',
                phone='+1234567890'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created!")
            print("  Email: admin@hostelhub.com")
            print("  Password: admin123")
        else:
            print("✓ Admin user already exists")
        
        # Add sample rooms if none exist
        if Room.query.count() == 0:
            sample_rooms = [
                Room(roomNumber='A-101', floor=1, capacity=2, type='double', price=1200.00),
                Room(roomNumber='A-102', floor=1, capacity=1, type='single', price=1500.00),
                Room(roomNumber='A-103', floor=1, capacity=3, type='triple', price=1000.00),
                Room(roomNumber='B-201', floor=2, capacity=2, type='double', price=1200.00),
                Room(roomNumber='B-202', floor=2, capacity=4, type='dorm', price=800.00),
            ]
            for room in sample_rooms:
                db.session.add(room)
            db.session.commit()
            print("✓ Sample rooms created!")
        else:
            print("✓ Rooms already exist")
        
        print("\n========================================")
        print("  HostelHub Database Initialized!")
        print("========================================")
        print("\nYou can now run the app with: python app.py")
        print("Then visit: http://localhost:5000")

if __name__ == '__main__':
    init_database()
