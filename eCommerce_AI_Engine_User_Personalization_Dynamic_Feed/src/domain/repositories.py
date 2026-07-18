from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ProductRepository(ABC):
    @abstractmethod
    async def get_personalized_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves a dynamically sorted product catalog based on user affinities."""
        pass

class UserAffinityRepository(ABC):
    @abstractmethod
    async def update_affinities(self, user_id: str, affinities: Dict[str, float]) -> None:
        """Upserts the latest AI-calculated affinities for a user."""
        pass