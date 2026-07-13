from typing import List, Optional
from collections import defaultdict
from app.core.database import SessionLocal
from app.models.asset import Asset as AssetModel, Metadata as MetadataModel

async def load_assets_by_job_ids(job_ids: List[str]) -> List[List[AssetModel]]:
    """
    DataLoader function to fetch Assets for multiple Job IDs in a single query.
    Solves the N+1 problem for Job -> Assets.
    """
    db = SessionLocal()
    try:
        # 1 Query for ALL assets across ALL requested jobs
        assets = db.query(AssetModel).filter(AssetModel.job_id.in_(job_ids)).all()
        
        # Group assets by job_id
        asset_map = defaultdict(list)
        for asset in assets:
            asset_map[asset.job_id].append(asset)
            
        # Return lists of assets in the exact order of the requested job_ids
        return [asset_map[job_id] for job_id in job_ids]
    finally:
        db.close()

async def load_metadata_by_asset_ids(asset_ids: List[int]) -> List[Optional[MetadataModel]]:
    """
    DataLoader function to fetch Metadata for multiple Asset IDs in a single query.
    Solves the N+1 problem for Asset -> Metadata.
    """
    db = SessionLocal()
    try:
        # 1 Query for ALL metadata across ALL requested assets
        metadata_records = db.query(MetadataModel).filter(MetadataModel.asset_id.in_(asset_ids)).all()
        
        # Map by asset_id
        meta_map = {meta.asset_id: meta for meta in metadata_records}
        
        # Return in the exact order of requested asset_ids
        return [meta_map.get(asset_id) for asset_id in asset_ids]
    finally:
        db.close()