from sqlalchemy import select

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    async def list_filtered(
        self, patient_id: int | None = None, category: str | None = None
    ) -> list[Document]:
        stmt = select(Document)
        if patient_id is not None:
            stmt = stmt.where(Document.patient_id == patient_id)
        if category is not None:
            stmt = stmt.where(Document.category == category)
        stmt = stmt.order_by(Document.uploaded_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
