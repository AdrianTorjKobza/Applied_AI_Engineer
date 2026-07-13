import uuid
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.request import CampaignLaunchRequest
from app.worker.tasks import process_omnichannel_campaign

router = APIRouter()

@router.post("/launch", status_code=status.HTTP_202_ACCEPTED)
def launch_campaign(
    request: CampaignLaunchRequest, 
    db: Session = Depends(get_db)
):
    """
    Accepts campaign requirements, creates a tracking Job, and delegates 
    the heavy AI generation to a background Celery worker.
    """
    # 1. Generate unique Job ID
    job_id = str(uuid.uuid4())

    # 2. Persist the initial state to DB
    new_job = Job(id=job_id, status=JobStatus.PENDING)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # 3. Queue the background task to Celery
    process_omnichannel_campaign.apply_async(
        args=[job_id, request.product_specs, request.target_audience],
        queue="ai_tasks"
    )

    # 4. Immediately return 202 Accepted so the client is not blocked
    return {
        "message": "Campaign generation started.",
        "job_id": job_id,
        "status": new_job.status
    }