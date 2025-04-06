from app import db
from flask_login import UserMixin
from datetime import datetime

# users model
class User(UserMixin, db.Model):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User %r>' % self.username

# requisition model
class Requisition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    office_name = db.Column(db.String(100), nullable=False)
    requested_by = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)  # New field for user email
    status = db.Column(db.String(20), default="Pending")  # Status tracking
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('RequisitionItems', backref='requisition', lazy=True)
    approvals = db.relationship('Approval', backref='requisition', lazy=True)

# Requisition items model
class RequisitionItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requisition_id = db.Column(db.Integer, db.ForeignKey('requisition.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(255))

# Approval model
class Approval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requisition_id = db.Column(db.Integer, db.ForeignKey('requisition.id'), nullable=False)
    approver_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # Approved/Not Approved
    signature = db.Column(db.String(255))  # Store as image path if needed
    date_signed = db.Column(db.DateTime, default=datetime.utcnow)