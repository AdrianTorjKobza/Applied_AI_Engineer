from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert

from src.domain.repositories import ProductRepository, UserAffinityRepository
from src.infrastructure.database.models import Product, UserAffinity

class PostgresProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_personalized_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        # 1. Fetch user affinities (fallback to default if new user)
        affinity_result = await self.session.execute(
            select(UserAffinity).where(UserAffinity.user_id == user_id)
        )
        user_affinity = affinity_result.scalar_one_or_none()
        
        if not user_affinity:
            user_affinity = UserAffinity(user_id=user_id) # Uses defaults (0.33)

        # 2. Dynamic Dot-Product Calculation in SQL
        match_score = (
            (Product.weight_running * user_affinity.score_running) +
            (Product.weight_weightlifting * user_affinity.score_weightlifting) +
            (Product.weight_outdoor * user_affinity.score_outdoor)
        ).label("dynamic_score")

        # 3. Query, sort, and limit entirely on the DB side
        query = select(Product, match_score).order_by(desc(match_score)).limit(limit)
        result = await self.session.execute(query)
        
        # 4. Map back to clean domain dictionaries
        feed = []
        for product, score in result.all():
            feed.append({
                "product_id": product.id,
                "name": product.name,
                "match_score": round(score, 3)
            })
        return feed

class PostgresUserAffinityRepository(UserAffinityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_affinities(self, user_id: str, affinities: Dict[str, float]) -> None:
        # PostgreSQL specific UPSERT (Insert on conflict update)
        stmt = insert(UserAffinity).values(
            user_id=user_id,
            score_running=affinities.get("running_gear", 0.0),
            score_weightlifting=affinities.get("weightlifting", 0.0),
            score_outdoor=affinities.get("outdoor", 0.0)
        )
        
        update_stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=dict(
                score_running=stmt.excluded.score_running,
                score_weightlifting=stmt.excluded.score_weightlifting,
                score_outdoor=stmt.excluded.score_outdoor
            )
        )
        
        await self.session.execute(update_stmt)
        await self.session.commit()