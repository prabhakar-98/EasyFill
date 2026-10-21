import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import delete

from app.database import connection as db_connection
from app.database.models.user import User
from app.database.models.user_data_embedding import UserDataEmbedding
from app.logging import get_logger
from app.security import get_current_user
from app.services.embedding import embedding_service

router = APIRouter()
logger = get_logger("routes_resume")

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "resumes"
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _extract_text_pdf(file_path: Path) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(str(file_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n".join(pages)


def _extract_text_docx(file_path: Path) -> str:
    from docx import Document

    doc = Document(str(file_path))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _chunk_text(text: str, max_chunk: int = 500) -> list[str]:
    """Split text into chunks by paragraphs, respecting max_chunk size."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 > max_chunk and current:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n{para}" if current else para

    if current:
        chunks.append(current)

    return chunks


@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    saved_name = f"{file_id}{ext}"
    file_path = user_dir / saved_name

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        if ext == ".pdf":
            text = _extract_text_pdf(file_path)
        else:
            text = _extract_text_docx(file_path)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.error("resume_parse_failed", error=str(e))
        raise HTTPException(status_code=422, detail="Failed to parse resume file")

    if not text.strip():
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="No text could be extracted from the file")

    chunks = _chunk_text(text)

    if not db_connection.async_session_factory:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # Clear old resume embeddings for this user
    async with db_connection.async_session_factory() as session:
        await session.execute(
            delete(UserDataEmbedding)
            .where(UserDataEmbedding.user_id == str(current_user.id))
            .where(UserDataEmbedding.source_type == "resume")
        )
        await session.commit()

    texts_to_embed = [f"resume: {chunk}" for chunk in chunks]
    embeddings = await embedding_service.embed_batch(texts_to_embed)

    async with db_connection.async_session_factory() as session:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            session.add(UserDataEmbedding(
                user_id=str(current_user.id),
                source_type="resume",
                source_id=file_id,
                field_key=f"resume_chunk_{i}",
                text_content=f"resume: {chunk}",
                embedding=embedding,
            ))
        await session.commit()

    logger.info(
        "resume_uploaded",
        user_id=str(current_user.id),
        file_id=file_id,
        filename=file.filename,
        text_length=len(text),
        chunks=len(chunks),
    )

    return {
        "status": "uploaded",
        "file_id": file_id,
        "filename": file.filename,
        "text_length": len(text),
        "chunks_embedded": len(chunks),
    }
