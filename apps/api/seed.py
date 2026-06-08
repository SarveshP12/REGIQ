"""Seed default tenant, admin user, and optional Neo4j demo graph.

Recommended (Docker — DB host `db`, all deps installed):

    docker compose exec api alembic upgrade head
    docker compose exec api python seed.py

Local run (requires Postgres on localhost + pip install -r requirements-docker.txt):

    set DATABASE_URL=postgresql+asyncpg://regiq_user:regiq_password@localhost:5432/regiq_db
    set NEO4J_URI=bolt://localhost:7687
    python seed.py

Default login after seed:
    Email:    admin@regiq.localhost
    Password: admin1234
"""

import asyncio
import os
import uuid as uuid_pkg

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User

SEED_ADMIN_EMAIL = "admin@regiq.localhost"
SEED_ADMIN_PASSWORD = "admin1234"


async def seed_data() -> None:
    async with async_session_factory() as db:
        print("Seeding database...")
        print(f"  DATABASE_URL host: {_db_host_hint()}")

        existing = await db.execute(select(User).where(User.email == SEED_ADMIN_EMAIL))
        if existing.scalar_one_or_none():
            print(f"  User {SEED_ADMIN_EMAIL} already exists — skipping tenant/user creation.")
        else:
            tenant_id = uuid_pkg.uuid4()
            tenant = Tenant(id=tenant_id, name="Default Seed Tenant", slug="default")
            db.add(tenant)
            user = User(
                id=uuid_pkg.uuid4(),
                email=SEED_ADMIN_EMAIL,
                name="Platform Admin",
                hashed_password=hash_password(SEED_ADMIN_PASSWORD),
                role="Super Admin",
                tenant_id=tenant_id,
                is_active=True,
            )
            db.add(user)
            print(f"  Created admin user: {SEED_ADMIN_EMAIL} / {SEED_ADMIN_PASSWORD}")

        if os.getenv("SKIP_NEO4J_SEED", "").lower() not in ("1", "true", "yes"):
            try:
                from app.services.graph_builder import GraphBuilderService

                builder = GraphBuilderService()
                builder.rebuild_default_graph()
                print("  Neo4j Incident Management demo graph seeded successfully.")
            except Exception as neo_e:
                print(f"  Skipping Neo4j seed: {neo_e}")
        else:
            print("  Neo4j seed skipped (SKIP_NEO4J_SEED set).")

        try:
            await db.commit()
            print("Seed completed successfully.")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding data: {e}")
            raise


def _db_host_hint() -> str:
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://regiq_user:regiq_password@db:5432/regiq_db")
    if "@" in url:
        return url.split("@", 1)[1].split("/", 1)[0]
    return url


if __name__ == "__main__":
    asyncio.run(seed_data())
