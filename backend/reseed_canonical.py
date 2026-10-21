"""One-time script to regenerate canonical embeddings with context-enriched format.

Run from backend/:
    python reseed_canonical.py
"""
import asyncio
import sys

sys.path.insert(0, ".")

from app.database.connection import init_db, close_db
from app.services.seed_canonical import seed_canonical_embeddings


async def main():
    await init_db()
    count = await seed_canonical_embeddings(force=True)
    print(f"Re-seeded {count} canonical embeddings with context-enriched format.")
    await close_db()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
