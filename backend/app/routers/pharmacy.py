from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pharmacy import PharmacyItem
from app.schemas.pharmacy import PharmacyItemCreate, PharmacyItemRead, PharmacyItemUpdate
from app.security.rbac import require_role

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"], dependencies=[Depends(require_role("admin", "receptionist"))])


@router.post("", response_model=PharmacyItemRead)
def create_item(payload: PharmacyItemCreate, db: Session = Depends(get_db)):
    if db.query(PharmacyItem).filter(PharmacyItem.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Item already exists")
    item = PharmacyItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[PharmacyItemRead])
def list_items(low_stock_only: bool = False, db: Session = Depends(get_db)):
    items = db.query(PharmacyItem).all()
    if low_stock_only:
        items = [i for i in items if i.is_low_stock]
    return items


@router.patch("/{item_id}", response_model=PharmacyItemRead)
def update_item(item_id: int, payload: PharmacyItemUpdate, db: Session = Depends(get_db)):
    item = db.get(PharmacyItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(PharmacyItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
