from app.models.inventory import Inventory
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    model = Inventory
