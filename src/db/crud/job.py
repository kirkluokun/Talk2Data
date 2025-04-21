from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List, Optional
from datetime import datetime, timezone

from src.db.models import Job
from src.schemas import JobUpdate
from src.schemas.job import JobStatus


async def create_or_update_job(
    db: AsyncSession, job_id: str, user_id: int, job_data: JobUpdate, conversation_id: Optional[int] = None
) -> Job:
    """Creates a new job or updates an existing one."""
    # Check if the job already exists for the user
    result = await db.execute(
        select(Job).filter(Job.id == job_id, Job.user_id == user_id)
    )
    db_job = result.scalars().first()

    if not db_job:
        # Create a new job
        creation_data = {
            "id": job_id,
            "user_id": user_id,
            "status": job_data.status or JobStatus.PENDING,
            "query_text": getattr(job_data, 'query_text', None),  # Safely access query_text
            "conversation_id": conversation_id,
            # Set other fields from job_data if provided, otherwise use defaults
            "progress": job_data.progress,
            "stage": job_data.stage,
            "started_at": job_data.started_at,
            "completed_at": job_data.completed_at,
            "result_type": job_data.result_type,
            "result_path": job_data.result_path,
            "result_content": job_data.result_content,
            "error_message": job_data.error_message,
        }
        # Filter out None values to rely on database defaults where applicable
        creation_data = {k: v for k, v in creation_data.items() if v is not None}

        db_job = Job(**creation_data)
        db.add(db_job)
        await db.flush()  # Flush to assign ID and apply defaults if needed
        await db.refresh(db_job) # Refresh to get the created object state
        return db_job
    else:
        # Update existing job
        # Use model_dump to get a dict of fields present in job_data
        update_data = job_data.model_dump(exclude_unset=True, exclude_none=True, exclude={'query_text'}) # Exclude query_text from direct update

        # Ensure status is Enum if provided
        if job_data.status is not None:
            update_data['status'] = job_data.status

        if update_data:
            await db.execute(
                update(Job)
                .where(Job.id == job_id, Job.user_id == user_id)
                .values(**update_data)
            )
            await db.flush()
            await db.refresh(db_job)

        return db_job

async def get_job_by_id_and_user(db: AsyncSession, job_id: str, user_id: int) -> Optional[Job]:
    """根据 ID 获取特定用户的 Job"""
    result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    return result.scalars().first()

async def get_jobs_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Job]:
    """获取特定用户的所有 Job 记录（分页）"""
    result = await db.execute(
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# Optional: Function to specifically update job status/progress/stage by Celery task
async def update_job_status(db: AsyncSession, job_id: str, status: JobStatus, progress: Optional[int] = None, stage: Optional[str] = None) -> Optional[Job]:
    """专门用于 Celery 任务更新状态、进度和阶段的函数，使用 JobStatus 枚举。"""
    values_to_update = {"status": status}
    if progress is not None:
        values_to_update["progress"] = progress
    if stage is not None:
        values_to_update["stage"] = stage

    current_time_utc = datetime.now(timezone.utc)
    # Mark start time if status is STARTED and start time is not set
    if status == JobStatus.STARTED:
         values_to_update["started_at"] = current_time_utc
         # Optional: Update only if started_at is NULL using where clause
         # stmt = update(Job).where(Job.id == job_id, Job.started_at.is_(None)).values(**values_to_update)
    elif status in [JobStatus.SUCCESS, JobStatus.FAILURE]:
        values_to_update["completed_at"] = current_time_utc

    stmt = update(Job).where(Job.id == job_id).values(**values_to_update)
    await db.execute(stmt)
    await db.flush()

    # Fetch the updated job - need user_id which is not passed here, maybe fetch without user check?
    # Or assume the caller (Celery task) knows the user_id? For now, return None or fetch just by job_id
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalars().first()
    if job:
        await db.refresh(job)
    return job 