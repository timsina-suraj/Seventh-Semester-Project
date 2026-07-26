from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    model = Patient

    async def get(self, id_: int) -> Patient | None:
        # Eager-load `user` (patient.user is accessed on every read/list —
        # lazy-loading it would need a second sync-style query, which
        # SQLAlchemy's async ORM can't do implicitly). Uses select() rather
        # than Session.get() because get() silently skips loader `options`
        # when the row is already in the identity map (e.g. right after
        # this same session created it), leaving `user` unloaded.
        result = await self.db.execute(
            select(Patient).options(selectinload(Patient.user)).where(Patient.id == id_)
        )
        return result.scalars().first()

    async def get_by_user_id(self, user_id: int) -> Patient | None:
        result = await self.db.execute(
            select(Patient).options(selectinload(Patient.user)).where(Patient.user_id == user_id)
        )
        return result.scalars().first()

    async def list_filtered(
        self, district: str | None = None, search: str | None = None, blood_group: str | None = None
    ) -> list[Patient]:
        """`search` matches full_name or patient_number (both plaintext
        columns — phone/address stay encrypted and aren't searchable this
        way, per Module 15's scope)."""
        stmt = select(Patient).options(selectinload(Patient.user))
        if district:
            stmt = stmt.where(Patient.district == district)
        if blood_group:
            stmt = stmt.where(Patient.blood_group == blood_group)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Patient.full_name.ilike(like), Patient.patient_number.ilike(like)))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def next_patient_number(self) -> str:
        """"PAT-{year}-{seq}", sequential within the current calendar year."""
        year = datetime.now(timezone.utc).year
        prefix = f"PAT-{year}-"
        count = await self.db.scalar(
            select(func.count()).select_from(Patient).where(Patient.patient_number.like(f"{prefix}%"))
        )
        return f"{prefix}{(count or 0) + 1:04d}"
