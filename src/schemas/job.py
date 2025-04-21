from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

# Define Job Status Enum
class JobStatus(str, Enum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"  # Task received by worker
    STARTED = "STARTED"    # Task started execution
    PROCESSING = "PROCESSING" # Custom state for intermediate processing
    SUCCESS = "SUCCESS"    # Task completed successfully
    FAILURE = "FAILURE"    # Task failed
    REVOKED = "REVOKED"    # Task revoked
    RETRY = "RETRY"        # Task is being retried

# Base schema for Job attributes
class JobBase(BaseModel):
    status: JobStatus # Use Enum
    progress: Optional[int] = None
    stage: Optional[str] = None
    result_type: Optional[str] = None
    result_path: Optional[str] = None
    result_content: Optional[str] = None # Consider Text or Any for flexibility
    error_message: Optional[str] = None


# Schema for creating/updating a job record in the DB (often done internally by the task)
# This schema reflects the fields most likely updated by the Celery task
class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None # Use Optional Enum
    progress: Optional[int] = None
    stage: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_type: Optional[str] = None
    result_path: Optional[str] = None
    result_content: Optional[str] = None # Consider Text or Any
    error_message: Optional[str] = None
    # Added query_text as it might be set during creation via update mechanism
    query_text: Optional[str] = None


# Schema for reading a job's details (includes DB-generated fields)
# This is likely what the /api/jobs/{job_id} endpoint will return
class Job(JobBase):
    id: str # Celery Task ID
    user_id: int
    conversation_id: Optional[int] # Added field
    query_text: Optional[str] # Added field
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Enable ORM mode
        use_enum_values = True # Ensure enum values are used when serializing

# Maybe a simpler schema for initial Job creation if done via API
# class JobCreate(BaseModel):
#     id: str # Celery Task ID
#     user_id: int
#     conversation_id: Optional[int] = None
#     query_text: Optional[str] = None
#     status: JobStatus = JobStatus.PENDING # Default status 