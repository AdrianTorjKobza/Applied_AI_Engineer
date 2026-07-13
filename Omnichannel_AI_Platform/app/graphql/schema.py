import asyncio
import strawberry
from typing import AsyncGenerator
from app.core.database import SessionLocal
from app.models.job import Job as JobModel, JobStatus
from app.graphql.types import JobType

@strawberry.type
class Query:
    @strawberry.field
    def job(self, id: str) -> JobType:
        """Standard GraphQL Query to fetch a Job by its ID."""
        db = SessionLocal()
        try:
            db_job = db.query(JobModel).filter(JobModel.id == id).first()
            if not db_job:
                raise Exception(f"Job {id} not found")
            return JobType(
                id=db_job.id,
                status=db_job.status.value,
                created_at=db_job.created_at,
                updated_at=db_job.updated_at
            )
        finally:
            db.close()

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def job_status(self, id: str) -> AsyncGenerator[JobType, None]:
        """
        WebSocket Subscription. Pushes updates to the client whenever the job status changes.
        In a purely local setup, we use an async generator polling the DB to avoid heavy Redis PubSub boilerplate.
        """
        last_status = None
        
        while True:
            db = SessionLocal()
            try:
                db_job = db.query(JobModel).filter(JobModel.id == id).first()
                if not db_job:
                    yield Exception("Job not found")
                    break

                current_status = db_job.status.value
                
                # Only yield to the WebSocket if the status actually changed
                if current_status != last_status:
                    yield JobType(
                        id=db_job.id,
                        status=current_status,
                        created_at=db_job.created_at,
                        updated_at=db_job.updated_at
                    )
                    last_status = current_status
                
                # Close connection if terminal state reached
                if current_status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                    break
                    
            finally:
                db.close()
            
            # Pause before querying again (Simulated PubSub)
            await asyncio.sleep(1.5)

schema = strawberry.Schema(query=Query, subscription=Subscription)