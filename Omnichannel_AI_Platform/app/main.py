from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.dataloader import DataLoader

from app.core.database import engine
from app.models.base import Base
from app.api.v1 import launch
from app.graphql.schema import schema
from app.graphql.dataloaders import load_assets_by_job_ids, load_metadata_by_asset_ids

# 1. Create DB Tables (Auto-migration for local development)
Base.metadata.create_all(bind=engine)

# 2. Initialize FastAPI Application
app = FastAPI(
    title="Omnichannel AI Platform",
    description="Scalable backend for generating AI marketing assets",
    version="1.0.0"
)

# 3. Define GraphQL Context dependency (Injects DataLoaders per request)
def get_graphql_context():
    return {
        "asset_loader": DataLoader(load_fn=load_assets_by_job_ids),
        "metadata_loader": DataLoader(load_fn=load_metadata_by_asset_ids),
    }

# 4. Configure Strawberry GraphQL Router
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    subscription_protocols=["graphql-ws"] # Modern WebSocket protocol
)

# 5. Wire up Routers
app.include_router(launch.router, prefix="/api/v1", tags=["Campaign"])
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Omnichannel AI Platform is running."}