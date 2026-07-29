from fastapi import APIRouter, Depends

from app.dependencies import get_pharmacy_service
from app.schemas.pharmacy import MedicineCreate, MedicineRead, MedicineStockUpdate
from app.security.rbac import require_role
from app.services.pharmacy_service import PharmacyService

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.post("", response_model=MedicineRead, dependencies=[Depends(require_role("admin", "receptionist"))])
async def create_medicine(payload: MedicineCreate, service: PharmacyService = Depends(get_pharmacy_service)):
    medicine = await service.create_medicine_with_stock(
        payload.name, payload.category, payload.expiry_date, payload.unit, payload.stock_quantity, payload.reorder_threshold
    )
    return MedicineRead.from_medicine(medicine)


@router.get("", response_model=list[MedicineRead], dependencies=[Depends(require_role("admin", "receptionist", "doctor"))])
async def list_medicines(
    low_stock_only: bool = False, search: str | None = None, service: PharmacyService = Depends(get_pharmacy_service)
):
    medicines = await service.list_medicines(search)
    items = [MedicineRead.from_medicine(m) for m in medicines]
    if low_stock_only:
        items = [i for i in items if i.is_low_stock]
    return items


@router.patch("/{medicine_id}", response_model=MedicineRead, dependencies=[Depends(require_role("admin", "receptionist"))])
async def update_stock(medicine_id: int, payload: MedicineStockUpdate, service: PharmacyService = Depends(get_pharmacy_service)):
    medicine = await service.update_stock(medicine_id, payload.stock_quantity, payload.reorder_threshold)
    return MedicineRead.from_medicine(medicine)


@router.delete("/{medicine_id}", status_code=204, dependencies=[Depends(require_role("admin", "receptionist"))])
async def delete_medicine(medicine_id: int, service: PharmacyService = Depends(get_pharmacy_service)):
    await service.delete_medicine(medicine_id)
