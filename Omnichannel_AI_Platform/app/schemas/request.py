from pydantic import BaseModel, Field

class CampaignLaunchRequest(BaseModel):
    product_specs: str = Field(
        ..., 
        description="Raw text document containing product specifications",
        example="A durable, water-resistant smartwatch with 7-day battery life."
    )
    target_audience: str = Field(
        ..., 
        description="The demographic or persona to target",
        example="Fitness enthusiasts and outdoor adventurers aged 20-40."
    )