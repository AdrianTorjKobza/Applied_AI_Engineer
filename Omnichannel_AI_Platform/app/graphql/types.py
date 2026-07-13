import strawberry
from typing import List, Optional
from datetime import datetime
from strawberry.types import Info

@strawberry.type
class MetadataType:
    id: int
    seo_tags: Optional[str]
    alt_text: Optional[str]
    json_ld: Optional[str]

@strawberry.type
class AssetType:
    id: int
    asset_type: str
    content: str
    created_at: datetime

    @strawberry.field
    async def metadata(self, info: Info) -> Optional[MetadataType]:
        """Resolves metadata efficiently using the DataLoader attached to the context."""
        loader = info.context["metadata_loader"]
        # .load() batches multiple single requests into one bulk DataLoader request
        db_metadata = await loader.load(self.id)
        if not db_metadata:
            return None
            
        return MetadataType(
            id=db_metadata.id,
            seo_tags=db_metadata.seo_tags,
            alt_text=db_metadata.alt_text,
            json_ld=db_metadata.json_ld
        )

@strawberry.type
class JobType:
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    @strawberry.field
    async def assets(self, info: Info) -> List[AssetType]:
        """Resolves assets efficiently using the DataLoader attached to the context."""
        loader = info.context["asset_loader"]
        db_assets = await loader.load(self.id)
        
        return [
            AssetType(
                id=asset.id,
                asset_type=asset.asset_type.value,
                content=asset.content,
                created_at=asset.created_at
            ) for asset in db_assets
        ]