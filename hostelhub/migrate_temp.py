import sys
sys.path.append('d:/hostelhub')
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN is_committee BOOLEAN DEFAULT 0;"))
        db.session.commit()
        print("Added is_committee to users")
    except Exception as e:
        print("users error:", e)
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE complaints ADD COLUMN is_escalated BOOLEAN DEFAULT 0;"))
        db.session.commit()
        print("Added is_escalated to complaints")
    except Exception as e:
        print("complaints error:", e)
        db.session.rollback()
