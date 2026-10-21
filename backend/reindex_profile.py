import asyncio
from app.database.connection import init_db
from app.services.indexing import index_user_profile


async def main():
    await init_db()
    count = await index_user_profile("75865b34-d044-409e-b034-da83facd8941")
    print(f"Indexed {count} fields")


asyncio.run(main())
