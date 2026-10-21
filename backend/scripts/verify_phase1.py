"""
Phase 1 Verification Script
----------------------------
Verifies: state imports, table creation, canonical seeding, similarity search.

Prerequisites:
  - docker-compose up -d postgres redis
  - ollama serve  (with nomic-embed-text pulled)

Run from backend/:
  ./venv/Scripts/python.exe scripts/verify_phase1.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main():
    passed = 0
    failed = 0

    # ── Step 1: State imports ──
    print("=" * 60)
    print("Step 1: Verify state schema imports")
    print("=" * 60)
    try:
        from app.workflows.state import (
            WorkflowState,
            FieldInput,
            MappedField,
            ResolvedField,
            FieldType,
            MappingSource,
            ValueSource,
            WorkflowStatus,
        )
        print("  WorkflowState   OK")
        print("  FieldInput      OK")
        print("  MappedField     OK")
        print("  ResolvedField   OK")
        print("  FieldType       OK")
        print("  MappingSource   OK")
        print("  ValueSource     OK")
        print("  WorkflowStatus  OK")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # ── Step 2: Schema imports ──
    print()
    print("=" * 60)
    print("Step 2: Verify shared API schemas")
    print("=" * 60)
    try:
        from app.api.schemas import (
            FieldInfo,
            AutofillRequest,
            AutofillResponse,
            WorkflowResponse,
        )
        f = FieldInfo(index=0, label="Email", type="text")
        print(f"  FieldInfo        OK  (sample: {f.model_dump()})")
        print("  AutofillRequest  OK")
        print("  AutofillResponse OK")
        print("  WorkflowResponse OK")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # ── Step 3: Prompt templates ──
    print()
    print("=" * 60)
    print("Step 3: Verify prompt templates")
    print("=" * 60)
    try:
        from app.models.prompts.field_mapping import (
            FIELD_MAPPING_SYSTEM_PROMPT,
            build_field_mapping_prompt,
        )
        from app.models.prompts.value_drafting import (
            VALUE_DRAFTING_SYSTEM_PROMPT,
            build_value_drafting_prompt,
        )

        fp = build_field_mapping_prompt(
            "Email Address", "Your work email", ["email", "phone", "full_name"]
        )
        print(f"  field_mapping prompt:\n    {fp[:80]}...")

        vp = build_value_drafting_prompt(
            field_label="Years of Experience",
            field_type="text",
            field_options=[],
            field_description=None,
            profile_context={"first_name": "John", "experience": "5"},
            rag_context=[],
        )
        print(f"  value_drafting prompt:\n    {vp[:80]}...")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # ── Step 4: Database + Table creation ──
    print()
    print("=" * 60)
    print("Step 4: Initialize database and create tables")
    print("=" * 60)
    try:
        from app.database.connection import init_db, engine
        from app.database.base import Base

        # Import all models so Base.metadata knows about them
        import app.database.models  # noqa: F401

        await init_db()

        from app.database.connection import engine as db_engine

        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("  Database connected    OK")
        print("  Tables created        OK")
        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        print("  Hint: Is PostgreSQL running? (docker-compose up -d postgres)")
        failed += 1
        print(f"\nResults: {passed} passed, {failed} failed")
        print("Skipping remaining steps (database required)")
        return

    # ── Step 5: Seed canonical embeddings ──
    print()
    print("=" * 60)
    print("Step 5: Seed canonical embeddings")
    print("=" * 60)
    try:
        from app.services.seed_canonical import seed_canonical_embeddings

        count = await seed_canonical_embeddings()
        if count > 0:
            print(f"  Seeded {count} rows    OK")
        else:
            print("  Already seeded (skipped)  OK")

        # Verify count
        from sqlalchemy import text as sql_text
        from app.database import connection as db_connection

        async with db_connection.async_session_factory() as session:
            result = await session.execute(
                sql_text("SELECT count(*) FROM canonical_embeddings")
            )
            total = result.scalar_one()
            print(f"  Total rows in table: {total}")

            result = await session.execute(
                sql_text(
                    "SELECT count(DISTINCT canonical_key) FROM canonical_embeddings"
                )
            )
            keys = result.scalar_one()
            print(f"  Distinct canonical keys: {keys}")

        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        print("  Hint: Is Ollama running with nomic-embed-text?")
        print("    ollama serve")
        print("    ollama pull nomic-embed-text")
        failed += 1

    # ── Step 6: Similarity search ──
    print()
    print("=" * 60)
    print("Step 6: Test similarity search")
    print("=" * 60)
    try:
        from app.services.embedding import embedding_service

        test_queries = [
            "email address",
            "phone number",
            "years of experience",
            "where do you see yourself in 5 years",
        ]

        for query in test_queries:
            emb = await embedding_service.embed(query)
            results = await embedding_service.search_canonical(
                emb, threshold=0.70, limit=3
            )
            print(f"\n  Query: \"{query}\"")
            if results:
                for r in results:
                    print(
                        f"    -> {r['canonical_key']:25s} "
                        f"sim={r['similarity']:.4f}  "
                        f"({r['label_text']})"
                    )
            else:
                print("    -> No matches above threshold")

        passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        failed += 1

    # ── Summary ──
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of 6 checks")
    print("=" * 60)

    if failed == 0:
        print("Phase 1 verification PASSED")
    else:
        print("Phase 1 verification has FAILURES — see above")


if __name__ == "__main__":
    asyncio.run(main())
