"""
Seed canonical_embeddings with known form label synonyms.

Usage:
    cd backend
    python -m scripts.seed_canonical_embeddings
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings
from app.database.connection import init_db
from app.database import connection as db_connection
from app.database.models.canonical_embedding import CanonicalEmbedding
from app.services.embedding import embedding_service
from sqlalchemy import select

SEED_DATA: dict[str, list[str]] = {
    "first name": [
        "first name", "given name", "fname",
    ],
    "last name": [
        "last name", "surname", "family name", "lname",
    ],
    "full name": [
        "full name", "your name", "applicant name", "legal name",
        "candidate name", "name",
    ],
    "email": [
        "email", "email address", "e-mail", "mail id",
        "email id", "contact email",
    ],
    "phone": [
        "phone", "phone number", "mobile", "mobile number",
        "cell phone", "contact number", "telephone",
        "whatsapp number", "tel",
    ],
    "location": [
        "location", "city", "current location", "current city",
        "where are you based", "place",
    ],
    "address": [
        "address", "mailing address", "street address",
        "residential address", "permanent address",
    ],
    "headline": [
        "headline", "professional headline", "tagline",
        "current role", "job title", "current designation",
        "designation", "role", "title",
    ],
    "bio": [
        "bio", "about", "about me", "summary",
        "professional summary", "about yourself",
    ],
    "skills": [
        "skills", "technical skills", "key skills",
        "core competencies", "technologies", "tech stack",
    ],
    "college": [
        "college", "university", "institution",
        "school name", "college name", "university name",
    ],
    "degree": [
        "degree", "qualification", "education level",
        "highest degree", "course", "program",
    ],
    "major": [
        "major", "branch", "specialization",
        "field of study", "stream", "department",
    ],
    "gpa": [
        "gpa", "cgpa", "grade", "percentage",
        "marks", "score", "academic score",
    ],
    "graduation year": [
        "graduation year", "year of graduation",
        "passing year", "year of passing",
        "graduation date", "expected graduation",
    ],
    "company": [
        "company", "current company", "employer",
        "organization", "current employer", "company name",
    ],
    "experience": [
        "experience", "years of experience", "work experience",
        "total experience", "professional experience",
    ],
    "linkedin": [
        "linkedin", "linkedin url", "linkedin profile",
        "linkedin link",
    ],
    "github": [
        "github", "github url", "github profile",
        "github link", "github username",
    ],
    "website": [
        "website", "portfolio", "personal website",
        "portfolio url", "portfolio link", "personal site",
    ],
    "salary expectation": [
        "salary expectation", "expected salary", "expected ctc",
        "salary requirement", "desired salary",
        "current ctc", "ctc expectation",
    ],
    "notice period": [
        "notice period", "availability to join",
        "when can you start", "when can you join",
        "earliest joining date", "start date",
        "availability",
    ],
    "gender": [
        "gender", "sex", "gender identity",
    ],
    "cover letter": [
        "cover letter", "letter of motivation",
        "motivation letter", "why should we hire you",
    ],
    "resume": [
        "resume", "cv", "curriculum vitae",
        "upload resume", "attach resume",
    ],
}


async def main():
    await init_db()
    service = embedding_service

    async with db_connection.async_session_factory() as session:
        existing = await session.execute(
            select(CanonicalEmbedding.label_text)
        )
        existing_labels = {row[0].lower() for row in existing}

    new_rows = []
    for canonical_key, labels in SEED_DATA.items():
        for label in labels:
            if label.lower() in existing_labels:
                continue
            new_rows.append((canonical_key, label))

    if not new_rows:
        print("All seed data already exists. Nothing to insert.")
        return

    print(f"Embedding {len(new_rows)} new labels...")

    texts = [label for _, label in new_rows]
    embeddings = await service.embed_batch(texts)

    async with db_connection.async_session_factory() as session:
        for (canonical_key, label), embedding in zip(new_rows, embeddings):
            row = CanonicalEmbedding(
                canonical_key=canonical_key,
                label_text=label,
                embedding=embedding,
                source="seed",
            )
            session.add(row)
        await session.commit()

    print(f"Inserted {len(new_rows)} canonical embeddings.")


if __name__ == "__main__":
    asyncio.run(main())
