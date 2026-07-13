import os
import uuid
import json
from app.core.celery_app import celery
from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.models.asset import Asset, AssetType, Metadata
from app.services.ollama_client import OllamaService

@celery.task(bind=True, max_retries=3)
def process_omnichannel_campaign(self, job_id: str, product_specs: str, target_audience: str):
    db = SessionLocal()
    try:
        # 1. Update Job Status to PROCESSING
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        job.status = JobStatus.PROCESSING
        db.commit()

        # 2. Initialize AI Service
        ai_service = OllamaService()

        # 3. Task A: Generate Blog Post (Text)
        blog_prompt = f"Write a 300-word marketing blog post for {target_audience} about a product with these specs: {product_specs}"
        blog_content = ai_service.generate_text(blog_prompt)
        
        text_asset = Asset(job_id=job_id, asset_type=AssetType.TEXT, content=blog_content)
        db.add(text_asset)
        db.commit() # Commit to get text_asset.id

        # 4. Task B: Generate SEO Metadata for the text
        seo_data = ai_service.generate_seo_metadata(blog_content)
        text_metadata = Metadata(
            asset_id=text_asset.id,
            seo_tags=json.dumps(seo_data.get("seo_tags", [])),
            alt_text=seo_data.get("alt_text", ""),
            json_ld=json.dumps(seo_data.get("json_ld", {}))
        )
        db.add(text_metadata)

        # 5. Task C: Generate Image (Simulated)
        # Note: Standard Ollama runs text models. For image generation, Stable Diffusion is typical.
        # Here we simulate the process of saving a generated image file to disk.
        image_filename = f"{uuid.uuid4()}.png"
        image_path = os.path.join("media", "assets", image_filename)

        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        # Simulate creating an image file
        with open(image_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR") # Fake PNG header for demonstration
        
        image_asset = Asset(job_id=job_id, asset_type=AssetType.IMAGE, content=f"/media/assets/{image_filename}")
        db.add(image_asset)
        db.commit()

        # 6. Mark Job as COMPLETED
        job.status = JobStatus.COMPLETED
        db.commit()

    except Exception as exc:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            db.commit()
        # Trigger Celery retry mechanism
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()