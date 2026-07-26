from app.core.exceptions import NotFoundError, ValidationError
from app.models.inventory import Inventory
from app.models.medicine import Medicine
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.medicine_repository import MedicineRepository


class PharmacyService:
    def __init__(self, medicine_repo: MedicineRepository, inventory_repo: InventoryRepository):
        self.medicine_repo = medicine_repo
        self.inventory_repo = inventory_repo

    async def create_medicine_with_stock(
        self,
        name: str,
        category: str | None,
        expiry_date,
        unit: str,
        stock_quantity: int,
        reorder_threshold: int,
    ) -> Medicine:
        """One-step create-medicine-plus-initial-inventory-row — preserves
        the pre-Phase-B single-form UX even though the schema is now split
        in two tables."""
        if await self.medicine_repo.get_by(name=name):
            raise ValidationError("A medicine with this name already exists")

        medicine = Medicine(name=name, category=category, expiry_date=expiry_date, unit=unit)
        self.medicine_repo.add(medicine)
        await self.medicine_repo.flush()

        self.inventory_repo.add(
            Inventory(medicine_id=medicine.id, quantity=stock_quantity, reorder_threshold=reorder_threshold)
        )
        await self.medicine_repo.commit()

        return await self.medicine_repo.get_with_inventory(medicine.id)

    async def list_medicines(self, search: str | None = None) -> list[Medicine]:
        return await self.medicine_repo.list_with_inventory(search)

    async def update_stock(self, medicine_id: int, quantity: int | None, reorder_threshold: int | None) -> Medicine:
        medicine = await self.medicine_repo.get_with_inventory(medicine_id)
        if not medicine:
            raise NotFoundError("Medicine not found")
        if not medicine.inventory:
            raise NotFoundError("This medicine has no inventory row")

        if quantity is not None:
            medicine.inventory.quantity = quantity
        if reorder_threshold is not None:
            medicine.inventory.reorder_threshold = reorder_threshold
        await self.medicine_repo.commit()

        return await self.medicine_repo.get_with_inventory(medicine_id)

    async def delete_medicine(self, medicine_id: int) -> None:
        medicine = await self.medicine_repo.get(medicine_id)
        if not medicine:
            raise NotFoundError("Medicine not found")
        await self.medicine_repo.delete(medicine)
        await self.medicine_repo.commit()
