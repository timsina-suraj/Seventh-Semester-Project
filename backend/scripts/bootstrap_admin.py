"""Creates the very first Admin account during system setup (Module 1:
'first admin account created during system setup; Admin creates all other
staff accounts'). Not exposed over the API — this is the one and only way
an Admin gets created without an existing Admin to do it.

Usage (from backend/, after `alembic upgrade head`):
    python -m scripts.bootstrap_admin --email admin@medishield.com --name "System Administrator"

The created account has no password yet and is inactive, exactly like any
other staff account — sign in with the same email to receive a first-login
OTP (see Module 3 OTP workflow) and set a password.
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.exceptions import AppError  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.repositories.audit_log_repository import AuditLogRepository  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402
from app.services.audit_service import AuditService  # noqa: E402
from app.services.registration_service import RegistrationService  # noqa: E402


async def bootstrap(email: str, name: str) -> None:
    async with SessionLocal() as db:
        service = RegistrationService(
            UserRepository(db), None, None, None, None, None, AuditService(AuditLogRepository(db))
        )
        try:
            user = await service.create_admin(email, name)
        except AppError as exc:
            print(f"Could not create admin: {exc.detail}")
            return
        print(f"Admin account created: {user.email} (id={user.id})")
        print("Sign in with this email to receive a first-login OTP and set a password.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    asyncio.run(bootstrap(args.email, args.name))


if __name__ == "__main__":
    main()
