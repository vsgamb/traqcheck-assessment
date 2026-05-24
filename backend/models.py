from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(200))
    designation = db.Column(db.String(200))
    skills = db.Column(db.Text)
    confidence_scores = db.Column(db.Text)
    resume_filename = db.Column(db.String(500))
    extraction_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    documents = db.relationship('Document', backref='candidate', lazy=True, cascade='all, delete-orphan')
    document_requests = db.relationship('DocumentRequest', backref='candidate', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'designation': self.designation,
            'skills': json.loads(self.skills) if self.skills else [],
            'confidence_scores': json.loads(self.confidence_scores) if self.confidence_scores else {},
            'resume_filename': self.resume_filename,
            'extraction_status': self.extraction_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'documents': [doc.to_dict() for doc in self.documents],
            'document_requests': [req.to_dict() for req in self.document_requests]
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    document_type = db.Column(db.String(50))
    filename = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'document_type': self.document_type,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class DocumentRequest(db.Model):
    __tablename__ = 'document_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    request_message = db.Column(db.Text)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='sent')
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'request_message': self.request_message,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'status': self.status
        }
