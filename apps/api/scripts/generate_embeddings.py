#!/usr/bin/env python3
"""Generate embeddings for all existing test cases using SBERT model and save to PostgreSQL."""

import asyncio
import sys
from pathlib import Path

# Allow running as script from apps/api
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session_factory
from app.models.test_case import TestCase
from app.core.ai.embedding import embedding_service
from sqlalchemy import select


async def main() -> None:
    print("Initializing embedding generation for existing test cases...")
    async with async_session_factory() as db:
        result = await db.execute(select(TestCase))
        test_cases = result.scalars().all()
        
        print(f"Found {len(test_cases)} test cases in database.")
        updated_count = 0
        
        for tc in test_cases:
            # Construct text representation
            text_repr = tc.title
            if tc.description:
                text_repr += f" {tc.description}"
            if tc.preconditions:
                text_repr += f" {tc.preconditions}"
            if tc.expected_results:
                text_repr += f" {tc.expected_results}"
            
            try:
                # Generate embedding
                embedding = embedding_service.generate_embedding(text_repr)
                tc.embedding = embedding
                updated_count += 1
            except Exception as e:
                print(f"Error generating embedding for Test Case ID {tc.id}: {e}")

        await db.commit()
        print(f"Successfully generated and saved embeddings for {updated_count} test cases.")


if __name__ == "__main__":
    asyncio.run(main())
