"""Script to enable PostgreSQL Row-Level Security (RLS) and policies for REGIQ tables."""

import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine

TABLES = [
    "users",
    "test_cases",
    "releases",
    "regression_suites",
    "execution_history",
    "change_sets",
    "business_processes",
    "audit_logs",
    "api_keys",
]


async def enable_rls():
    print("Connecting to database and enabling Row-Level Security (RLS)...")
    async with engine.begin() as conn:
        for table in TABLES:
            try:
                # Enable RLS
                await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
                # Force RLS for all users (including owner/superuser)
                await conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))
                # Drop existing isolation policy if any
                await conn.execute(text(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};"))
                # Create the isolation policy based on 'app.current_tenant_id'
                await conn.execute(text(f"""
                    CREATE POLICY {table}_tenant_isolation ON {table}
                    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
                """))
                print(f" Successfully enabled RLS and isolation policy on table '{table}'")
            except Exception as e:
                print(f"❌ Error setting RLS on table '{table}': {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(enable_rls())
