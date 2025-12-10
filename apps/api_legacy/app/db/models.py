"""
SentryAI Database Models
SQLAlchemy models for PostgreSQL
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum
import uuid

from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# --- Enums ---

class JobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DocumentStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


# --- Models ---

class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    projects = relationship("Project", back_populates="owner")
    

class Project(Base):
    """Security project / workspace"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_scope = Column(JSONB)  # List of allowed targets/domains
    graph_id = Column(String(255))  # Reference to Neo4j root node
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", back_populates="projects")
    jobs = relationship("Job", back_populates="project")
    findings = relationship("Finding", back_populates="project")
    documents = relationship("Document", back_populates="project")


class Job(Base):
    """Scan/mission job tracking"""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    job_type = Column(String(100))  # scan, recon, audit, etc.
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    
    # Temporal integration
    temporal_workflow_id = Column(String(255), unique=True, index=True)
    temporal_run_id = Column(String(255))
    
    # Execution details
    target = Column(String(255))
    config = Column(JSONB)  # Job configuration/parameters
    result = Column(JSONB)  # Job result summary
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Logs storage
    logs_path = Column(String(500))  # S3 or local path for archived logs

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    # Relationships
    project = relationship("Project", back_populates="jobs")
    findings = relationship("Finding", back_populates="job")


class Finding(Base):
    """Security finding / vulnerability"""
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Classification
    severity = Column(Enum(Severity), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Location
    host = Column(String(255), index=True)
    port = Column(Integer)
    path = Column(String(1000))
    url = Column(String(2000))
    
    # Source
    tool_source = Column(String(100))  # nuclei, nmap, custom, etc.
    template_id = Column(String(255))  # e.g., nuclei template ID
    
    # Evidence
    raw_output = Column(JSONB)  # Full tool output
    evidence = Column(Text)  # HTTP request/response
    screenshot_path = Column(String(500))
    
    # Remediation
    remediation = Column(Text)
    cwe_id = Column(String(50))
    cvss_score = Column(String(10))
    
    # Status
    status = Column(String(50), default="new")  # new, confirmed, false_positive, resolved
    is_duplicate = Column(Boolean, default=False)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))

    # Relationships
    project = relationship("Project", back_populates="findings")
    job = relationship("Job", back_populates="findings")


class Document(Base):
    """Knowledge base document for RAG"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # File info
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50))  # yaml, json, pdf, md, csv
    file_size = Column(Integer)
    file_path = Column(String(1000))  # Storage path
    
    # Processing
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Weaviate reference
    weaviate_class = Column(String(255))  # Collection/class name
    
    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    # Relationships
    project = relationship("Project", back_populates="documents")


class Agent(Base):
    """AI Agent configuration"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    role = Column(String(100))  # auditor, recon, planner, etc.
    description = Column(Text)
    
    # Configuration
    system_prompt = Column(Text)
    model = Column(String(100), default="mistralai/mixtral-8x22b-instruct-v0.1")
    temperature = Column(String(10), default="0.2")
    
    # Tool access
    allowed_tools = Column(JSONB, default=[])  # List of tool IDs
    knowledge_auto = Column(Boolean, default=True)
    tools_auto = Column(Boolean, default=True)
    
    # Team
    team = Column(String(50))  # neo (red), mirage (blue)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Tool(Base):
    """Security tool registry"""
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    
    # Source
    github_repo = Column(String(500))
    docker_image = Column(String(500))
    binary_path = Column(String(500))
    
    # Configuration
    version = Column(String(50))
    install_command = Column(Text)
    wrapper_config = Column(JSONB)  # How to invoke the tool
    
    # Status
    status = Column(String(50), default="ready")  # installing, ready, failed
    is_builtin = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Schedule(Base):
    """Scheduled scan configuration"""
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    
    # Target
    target = Column(String(500))
    scan_config = Column(JSONB)
    
    # Schedule
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    
    # Temporal
    temporal_schedule_id = Column(String(255), unique=True)
    
    # Options
    auto_pilot = Column(Boolean, default=True)  # Skip human approval
    enabled = Column(Boolean, default=True)
    
    # Stats
    last_run_at = Column(DateTime(timezone=True))
    last_status = Column(String(50))
    run_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))


class Integration(Base):
    """External integrations (Slack, Jira, etc.)"""
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    type = Column(String(50), nullable=False)  # slack, jira, linear, discord, webhook
    name = Column(String(255), nullable=False)
    
    # Configuration (encrypted in production)
    config = Column(JSONB, nullable=False)
    
    # Event subscriptions
    events = Column(JSONB, default=[])  # List of event types
    
    enabled = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
