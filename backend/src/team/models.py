from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..core.database import Base

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(String, primary_key=True, index=True)
    organization_owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Invitation Details
    email = Column(String(100), nullable=False)
    invitation_token = Column(String(255), nullable=True)
    
    # Role & Permissions
    role = Column(String(20), default="user")  # admin, manager, user, viewer
    permissions = Column(JSON, nullable=True)  # Custom permissions object
    
    # Status Tracking
    status = Column(String(20), default="pending")  # pending, active, inactive, suspended
    
    # Department & Job Info
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    
    # Timestamps
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization_owner = relationship("User", foreign_keys=[organization_owner_id])
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<TeamMember(id={self.id}, email={self.email}, role={self.role})>"

class TeamInvitation(Base):
    __tablename__ = "team_invitations"
    
    id = Column(String, primary_key=True, index=True)
    team_member_id = Column(String, ForeignKey("team_members.id", ondelete="CASCADE"))
    
    # Invitation tracking
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    team_member = relationship("TeamMember")
    
    def __repr__(self):
        return f"<TeamInvitation(id={self.id}, team_member_id={self.team_member_id})>" 