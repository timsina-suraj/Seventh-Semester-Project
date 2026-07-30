"""Module 12: file uploads stored on local disk, metadata in the DB. Files
are named by a random token on disk (`stored_filename`) so the filesystem
path alone never reveals the original filename or lets one guess another
document's URL — access is always mediated by the `Document.id` + an
authorization check in the router."""
import secrets
from pathlib import Path

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.document import VALID_DOCUMENT_CATEGORIES, Document
from app.repositories.document_repository import DocumentRepository

logger = get_logger(__name__)

# Extension -> acceptable magic-byte prefixes. Checked against the file's
# *actual* bytes, not the client-supplied content_type header or filename
# alone -- either of those can be forged (an .exe renamed to report.pdf still
# claims content_type="application/pdf" if the caller sets it that way), so
# only sniffing the real bytes actually stops that.
_ALLOWED_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".pdf": (b"%PDF",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
}


def _validate_file_type(original_filename: str, content: bytes) -> None:
    suffix = Path(original_filename).suffix.lower()
    signatures = _ALLOWED_SIGNATURES.get(suffix)
    if signatures is None:
        allowed = ", ".join(sorted({s.lstrip(".").upper() for s in _ALLOWED_SIGNATURES}))
        raise ValidationError(f"Unsupported file type '{suffix or '(none)'}' — only {allowed} files are accepted")
    if not any(content.startswith(sig) for sig in signatures):
        raise ValidationError(
            f"File content does not match its '{suffix}' extension — the upload may be corrupted, "
            "mislabeled, or not actually the file type it claims to be"
        )


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


class DocumentService:
    def __init__(self, document_repo: DocumentRepository):
        self.document_repo = document_repo

    async def upload(
        self,
        patient_id: int,
        category: str,
        original_filename: str,
        content_type: str,
        content: bytes,
        uploaded_by_user_id: int,
    ) -> Document:
        if category not in VALID_DOCUMENT_CATEGORIES:
            raise ValidationError(f"category must be one of {VALID_DOCUMENT_CATEGORIES}")

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(f"File exceeds the {settings.max_upload_size_mb}MB upload limit")
        if len(content) == 0:
            raise ValidationError("Uploaded file is empty")
        _validate_file_type(original_filename, content)

        suffix = Path(original_filename).suffix[:16]
        stored_filename = f"{secrets.token_hex(16)}{suffix}"
        (_upload_root() / stored_filename).write_bytes(content)

        document = Document(
            patient_id=patient_id,
            uploaded_by_user_id=uploaded_by_user_id,
            category=category,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type or "application/octet-stream",
            file_size=len(content),
        )
        self.document_repo.add(document)
        await self.document_repo.commit()
        await self.document_repo.refresh(document)
        logger.info("document_uploaded patient_id=%s category=%s size=%s", patient_id, category, len(content))
        return document

    async def list_filtered(self, patient_id: int | None = None, category: str | None = None) -> list[Document]:
        return await self.document_repo.list_filtered(patient_id, category)

    async def get_or_404(self, document_id: int) -> Document:
        document = await self.document_repo.get(document_id)
        if not document:
            raise NotFoundError("Document not found")
        return document

    def read_file(self, document: Document) -> bytes:
        path = _upload_root() / document.stored_filename
        if not path.exists():
            raise NotFoundError("Document file is missing from storage")
        return path.read_bytes()

    async def delete(self, document: Document) -> None:
        path = _upload_root() / document.stored_filename
        path.unlink(missing_ok=True)
        await self.document_repo.delete(document)
        await self.document_repo.commit()
