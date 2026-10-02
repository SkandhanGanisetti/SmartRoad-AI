from datetime import datetime
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True); name = Column(String, nullable=False); email = Column(String, unique=True); role = Column(String, default='citizen'); created_at = Column(DateTime, default=datetime.utcnow)
    complaints = relationship('Complaint', back_populates='reporter')

class Complaint(Base):
    __tablename__ = 'complaints'
    id = Column(Integer, primary_key=True); ticket_id = Column(String, unique=True, nullable=False); title = Column(String, nullable=False); damage_types = Column(JSON, default=list); severity = Column(String, default='Low'); severity_score = Column(Float, default=0); priority = Column(String, default='Low'); status = Column(String, default='Reported'); latitude = Column(Float); longitude = Column(Float); address = Column(String, default=''); original_image = Column(String); annotated_image = Column(String); confidence = Column(Float, default=0); damage_coverage = Column(Float, default=0); detection_count = Column(Integer, default=0); detection_json = Column(JSON, default=list); reporter_id = Column(Integer, ForeignKey('users.id')); is_duplicate = Column(Boolean, default=False); duplicate_of = Column(Integer, ForeignKey('complaints.id')); is_demo = Column(Boolean, default=False); created_at = Column(DateTime, default=datetime.utcnow); updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reporter = relationship('User', back_populates='complaints'); repairs = relationship('Repair', back_populates='complaint', cascade='all, delete-orphan')

class Repair(Base):
    __tablename__ = 'repairs'
    id = Column(Integer, primary_key=True); complaint_id = Column(Integer, ForeignKey('complaints.id'), nullable=False); before_image = Column(String); before_annotated = Column(String); after_image = Column(String); after_annotated = Column(String); before_coverage = Column(Float, default=0); after_coverage = Column(Float, default=0); improvement_percent = Column(Float, default=0); verification_status = Column(String, default='Needs Review'); verification_notes = Column(Text, default=''); verified_at = Column(DateTime); created_at = Column(DateTime, default=datetime.utcnow)
    complaint = relationship('Complaint', back_populates='repairs')
