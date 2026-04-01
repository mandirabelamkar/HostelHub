from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'admin', name='user_roles'), default='student')
    enrollmentNumber = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    purpose = db.Column(db.String(255), nullable=True)
    is_committee = db.Column(db.Boolean, default=False)
    

    # Foreign key to Room
    roomId = db.Column(db.String(36), db.ForeignKey('rooms.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    room = db.relationship('Room', backref=db.backref('occupants', lazy=True))

    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    roomNumber = db.Column(db.String(50), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=2)
    type = db.Column(db.Enum('single', 'double', 'triple', 'dorm', name='room_types'), default='double')
    price = db.Column(db.Float, nullable=False)
    features = db.Column(db.JSON, nullable=True)
    floor = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.Enum('Electrical', 'Plumbing', 'Carpentry', 'Cleaning', 'Maintenance', 'Internet', 'Other', name='complaint_categories'), nullable=False)
    status = db.Column(db.Enum('Pending', 'In Progress', 'Resolved', 'Rejected', name='complaint_statuses'), default='Pending')
    resolutionRemarks = db.Column(db.Text, nullable=True)
    is_escalated = db.Column(db.Boolean, default=False)
    
    userId = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    resolvedById = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    student = db.relationship('User', foreign_keys=[userId], backref=db.backref('complaints', lazy=True))
    resolvedBy = db.relationship('User', foreign_keys=[resolvedById], backref=db.backref('resolvedComplaints', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
 
class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum('General', 'Urgent', 'Event', 'Maintenance', 'Fee', 'News', name='notice_categories'), default='General')
    isImportant = db.Column(db.Boolean, default=False)
    expiresAt = db.Column(db.DateTime, nullable=True)
    
    createdById = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', foreign_keys=[createdById], backref=db.backref('notices', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    userId = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    type = db.Column(db.String(50), default='info') # info, warning, success
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    semester = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.Enum('Hostel Fee', 'Mess Fee', 'Fine', 'Other', name='fee_types'), default='Hostel Fee')
    status = db.Column(db.Enum('Pending', 'Paid', 'Overdue', name='fee_statuses'), default='Pending')
    dueDate = db.Column(db.DateTime, nullable=False)
    paymentDate = db.Column(db.DateTime, nullable=True)
    transactionId = db.Column(db.String(100), nullable=True)
    
    userId = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    student = db.relationship('User', foreign_keys=[userId], backref=db.backref('fees', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Letter(db.Model):
    __tablename__ = 'letters'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum('Leave Request', 'Clearance', 'Bonafide', 'Room Change', 'Other', name='letter_categories'), default='Other')
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected', name='letter_statuses'), default='Pending')
    adminRemarks = db.Column(db.Text, nullable=True)

    userId = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reviewedById = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    student = db.relationship('User', foreign_keys=[userId], backref=db.backref('letters', lazy=True))
    reviewedBy = db.relationship('User', foreign_keys=[reviewedById], backref=db.backref('reviewedLetters', lazy=True))

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
