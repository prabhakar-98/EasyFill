from sqlalchemy import select, delete

from app.database import connection as db_connection
from app.database.models.user import User
from app.database.models.user_profile import UserProfile
from app.database.models.user_data_embedding import UserDataEmbedding
from app.logging import get_logger
from app.services.embedding import embedding_service

logger = get_logger("indexing")


async def index_user_profile(user_id: str) -> int:
    """Embed profile fields + professional_data into user_data_embeddings."""
    if not db_connection.async_session_factory:
        return 0

    async with db_connection.async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return 0

        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return 0

    pairs: list[tuple[str, str]] = []

    if profile.first_name:
        pairs.append(("first_name", f"first name: {profile.first_name}"))
    if profile.last_name:
        pairs.append(("last_name", f"last name: {profile.last_name}"))
    if profile.first_name and profile.last_name:
        pairs.append(("full_name", f"full name: {profile.first_name} {profile.last_name}"))
    if user.email:
        pairs.append(("email", f"email: {user.email}"))
    if profile.phone:
        pairs.append(("phone", f"phone: {profile.phone}"))
    if profile.location:
        pairs.append(("location", f"location: {profile.location}"))

    pro = profile.professional_data or {}
    for key, value in pro.items():
        if value:
            if isinstance(value, list):
                text_val = ", ".join(str(v) for v in value)
            elif isinstance(value, str):
                text_val = value
            else:
                text_val = str(value)
            pairs.append((key, f"{key}: {text_val}"))

    if not pairs:
        return 0

    # Clear old profile embeddings for this user
    async with db_connection.async_session_factory() as session:
        await session.execute(
            delete(UserDataEmbedding)
            .where(UserDataEmbedding.user_id == user_id)
            .where(UserDataEmbedding.source_type == "profile")
        )
        await session.commit()

    texts = [text for _, text in pairs]
    embeddings = await embedding_service.embed_batch(texts)

    async with db_connection.async_session_factory() as session:
        for (field_key, text_content), embedding in zip(pairs, embeddings):
            row = UserDataEmbedding(
                user_id=user_id,
                source_type="profile",
                field_key=field_key,
                text_content=text_content,
                embedding=embedding,
            )
            session.add(row)
        await session.commit()

    logger.info("profile_indexed", user_id=user_id, fields=len(pairs))
    return len(pairs)


async def index_memory(user_id: str, key: str, value: str) -> None:
    """Embed a single personalized memory into user_data_embeddings."""
    if not db_connection.async_session_factory:
        return

    text_content = f"{key}: {value}"
    embedding = await embedding_service.embed(text_content)

    async with db_connection.async_session_factory() as session:
        # Upsert: remove old entry for same key
        await session.execute(
            delete(UserDataEmbedding)
            .where(UserDataEmbedding.user_id == user_id)
            .where(UserDataEmbedding.source_type == "memory")
            .where(UserDataEmbedding.field_key == key)
        )

        row = UserDataEmbedding(
            user_id=user_id,
            source_type="memory",
            field_key=key,
            text_content=text_content,
            embedding=embedding,
        )
        session.add(row)
        await session.commit()

    logger.info("memory_indexed", user_id=user_id, key=key)


SIMILARITY_SKIP_THRESHOLD = 0.9


async def smart_index_memory(user_id: str, field: str, value: str) -> str:
    """Index memory only when similar data doesn't already exist.

    Returns "skipped", "updated", or "saved".
    """
    if not db_connection.async_session_factory:
        return "skipped"

    text_content = f"{field}: {value}"
    embedding = await embedding_service.embed(text_content)

    results = await embedding_service.search_user_data(
        user_id=user_id,
        query_embedding=embedding,
        threshold=SIMILARITY_SKIP_THRESHOLD,
        limit=1,
    )

    if results and results[0]["similarity"] >= SIMILARITY_SKIP_THRESHOLD:
        logger.info(
            "smart_index_skipped",
            user_id=user_id,
            field=field,
            existing_similarity=results[0]["similarity"],
        )
        return "skipped"

    async with db_connection.async_session_factory() as session:
        await session.execute(
            delete(UserDataEmbedding)
            .where(UserDataEmbedding.user_id == user_id)
            .where(UserDataEmbedding.source_type == "memory")
            .where(UserDataEmbedding.field_key == field)
        )

        row = UserDataEmbedding(
            user_id=user_id,
            source_type="memory",
            field_key=field,
            text_content=text_content,
            embedding=embedding,
        )
        session.add(row)
        await session.commit()

    logger.info("smart_index_saved", user_id=user_id, field=field)
    return "saved"


async def index_preference(user_id: str, key: str, value: str) -> None:
    """Embed a single user preference into user_data_embeddings."""
    if not db_connection.async_session_factory:
        return

    text_content = f"{key}: {value}"
    embedding = await embedding_service.embed(text_content)

    async with db_connection.async_session_factory() as session:
        await session.execute(
            delete(UserDataEmbedding)
            .where(UserDataEmbedding.user_id == user_id)
            .where(UserDataEmbedding.source_type == "preference")
            .where(UserDataEmbedding.field_key == key)
        )

        row = UserDataEmbedding(
            user_id=user_id,
            source_type="preference",
            field_key=key,
            text_content=text_content,
            embedding=embedding,
        )
        session.add(row)
        await session.commit()

    logger.info("preference_indexed", user_id=user_id, key=key)


async def index_application_fields(
    user_id: str,
    application_id: str,
    field_answers: dict[str, str],
) -> int:
    """Embed all answered fields from a completed form into user_data_embeddings."""
    if not db_connection.async_session_factory or not field_answers:
        return 0

    pairs = []
    for label, value in field_answers.items():
        if value:
            text_val = ", ".join(value) if isinstance(value, list) else value
            pairs.append((label.lower().strip(), f"{label}: {text_val}"))

    if not pairs:
        return 0

    texts = [text for _, text in pairs]
    embeddings = await embedding_service.embed_batch(texts)

    async with db_connection.async_session_factory() as session:
        for (field_key, text_content), embedding in zip(pairs, embeddings):
            row = UserDataEmbedding(
                user_id=user_id,
                source_type="application",
                source_id=application_id,
                field_key=field_key,
                text_content=text_content,
                embedding=embedding,
            )
            session.add(row)
        await session.commit()

    logger.info(
        "application_indexed",
        user_id=user_id,
        application_id=application_id,
        fields=len(pairs),
    )
    return len(pairs)
