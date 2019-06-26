# app/models.py
import uuid
			
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy		# This is already included in the blueprint
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate(db=db)

# Define your models here
class Contact(db.Model):
    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(100))
    address = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(50))

    def __repr__(self):
        return f'<Contact {self.first_name} {self.last_name}>'

class Appointment(db.Model):
    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=False)
    organization_uuid = db.Column(UUID(as_uuid=True))
    contact_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('contact.uuid'), nullable=False)
    contact = db.relationship('Contact', backref=db.backref('appointments', lazy=True))

    def __repr__(self):
        return f'<Appointment {self.name}>'

