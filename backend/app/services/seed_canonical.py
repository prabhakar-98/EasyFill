from sqlalchemy import func, select

from app.database import connection as db_connection
from app.database.models.canonical_embedding import CanonicalEmbedding
from app.logging import get_logger
from app.services.embedding import embedding_service

logger = get_logger("seed_canonical")


# Each canonical field has: key, description (what it means), aliases (label variants)
CANONICAL_FIELDS: list[tuple[str, str, list[str]]] = [
    ("first_name",
     "person's first or given name",
     ["First Name", "Given Name", "Your first name",
      "First name", "What is your first name?"]),

    ("last_name",
     "person's last name, surname, or family name",
     ["Last Name", "Surname", "Family Name",
      "Last name", "What is your last name?"]),

    ("full_name",
     "person's complete full name including first and last name",
     ["Full Name", "Name", "Your name",
      "Full name", "What is your name?", "Your full name"]),

    ("email",
     "email address for contact and communication",
     ["Email", "Email Address", "Your email",
      "E-mail", "Email ID", "What is your email address?"]),

    ("phone",
     "phone number or mobile number for contact",
     ["Phone", "Phone Number", "Mobile",
      "Contact Number", "Mobile Number", "Cell Phone",
      "What is your phone number?", "Telephone"]),

    ("location",
     "city, address, or current geographic location where the person lives",
     ["Location", "City", "Address",
      "Where are you based?", "Current Location",
      "Your city", "Where do you live?"]),

    ("linkedin",
     "LinkedIn social media profile URL",
     ["LinkedIn", "LinkedIn URL", "LinkedIn Profile",
      "LinkedIn profile URL", "Your LinkedIn"]),

    ("github",
     "GitHub code repository profile URL or username",
     ["GitHub", "GitHub URL", "GitHub Profile",
      "GitHub profile URL", "Your GitHub", "Github Username"]),

    ("website",
     "personal website, portfolio website, or blog URL",
     ["Website", "Portfolio", "Personal Website",
      "Portfolio URL", "Your website", "Blog"]),

    ("university",
     "university, college, or educational institution name where the person studied",
     ["University", "College", "School",
      "Institution", "Educational Institution",
      "Where did you study?", "Alma Mater"]),

    ("degree",
     "academic degree or qualification such as B.Tech, MBA, PhD, Masters",
     ["Degree", "Qualification", "Academic Degree",
      "Highest Degree", "What degree do you hold?", "Course"]),

    ("gpa",
     "GPA, CGPA, or academic grade point average score",
     ["GPA", "CGPA", "Grade Point Average",
      "Grades", "Academic Score", "Your GPA"]),

    ("graduation_year",
     "year of graduation, year of passing, or expected graduation year",
     ["Graduation Year", "Year of Graduation",
      "Expected Graduation", "When did you graduate?",
      "Graduation Date", "Year of passing", "Passout Year", "Passout"]),

    ("company",
     "current or most recent company, organization, or employer name",
     ["Company", "Current Company", "Organization",
      "Employer", "Where do you work?",
      "Company Name", "Current Employer"]),

    ("experience",
     "total number of years of professional work experience",
     ["Years of Experience", "Work Experience",
      "How many years of experience do you have?",
      "Total Experience",
      "How many years have you worked professionally?"]),

    ("certifications",
     "professional certifications, certificates, courses completed, or credentials earned",
     ["Certifications", "Certificates", "Professional Certifications",
      "Courses Completed", "Credentials",
      "List your certifications", "Professional certificates"]),

    ("achievements",
     "awards, achievements, honors, or notable accomplishments",
     ["Achievements", "Awards", "Honors",
      "Accomplishments", "Notable Achievements"]),

    ("salary_expectation",
     "expected salary, desired compensation, or CTC expectation in currency",
     [
         "Expected Salary", "Salary Expectation",
      "Desired Compensation", "CTC Expectation",
      "What is your expected salary?"]),

    ("notice_period",
     "notice period duration or availability timeline to join a new role",
     ["Notice Period", "Availability",
      "When can you join?", "How soon can you start?",
      "Current Notice Period"]),

    ("gender",
     "gender or gender identity of the person",
     ["Gender", "Sex",
      "What is your gender?", "Gender Identity"]),

    ("date_of_birth",
     "date of birth, birthday, or birth date of the person",
     ["Date of Birth", "DOB", "Birthday",
      "Birth Date", "When were you born?"]),

    ("cover_letter",
     "cover letter, letter of motivation, or statement of interest for a role",
     ["Cover Letter", "Letter of Motivation",
      "Why do you want this role?",
      "Why should we hire you?"]),

    ("start_date",
     "preferred or earliest available start date to begin work",
     ["Start Date", "Available Start Date",
      "When can you start?", "Preferred Start Date",
      "Earliest Start Date"]),

    ("work_authorization",
     "work authorization status, visa status, or sponsorship requirement",
     ["Work Authorization", "Are you authorized to work?",
      "Visa Status", "Work Permit",
      "Do you require sponsorship?"]),

    ("relocation",
     "willingness to relocate to a different city or country for work",
     ["Willing to Relocate", "Open to Relocation",
      "Can you relocate?", "Relocation"]),

    ("remote_preference",
     "preferred work mode such as remote, onsite, or hybrid arrangement",
     ["Remote", "Work Preference",
      "Remote/Onsite/Hybrid", "Preferred Work Mode",
      "Are you open to remote work?"]),

]

# Lookup helpers consumed by map_fields
ALL_CANONICAL_KEYS = [key for key, _, _ in CANONICAL_FIELDS]
CANONICAL_DESCRIPTIONS = {key: desc for key, desc, _ in CANONICAL_FIELDS}

# Build alias → canonical_key lookup for deterministic matching
ALIAS_MAP: dict[str, str] = {}
for _key, _desc, _aliases in CANONICAL_FIELDS:
    ALIAS_MAP[_key.lower().replace("_", " ")] = _key
    for _alias in _aliases:
        normalized = " ".join(_alias.lower().strip().split())
        ALIAS_MAP[normalized] = _key


def build_canonical_text(key: str, description: str) -> str:
    """Build context-enriched text for embedding a canonical key."""
    return f"Canonical key: {key}. Meaning: {description}"


async def seed_canonical_embeddings(force: bool = False) -> int:
    if not db_connection.async_session_factory:
        logger.warning("seed_skipped", reason="database not initialized")
        return 0

    async with db_connection.async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(CanonicalEmbedding)
        )
        existing_count = result.scalar_one()

        if existing_count > 0 and not force:
            logger.info(
                "seed_skipped",
                reason="canonical_embeddings already populated",
                count=existing_count,
            )
            return 0

        if force and existing_count > 0:
            from sqlalchemy import delete
            await session.execute(delete(CanonicalEmbedding))
            await session.commit()
            logger.info("seed_cleared", deleted=existing_count)

    # Build pairs: each alias gets embedded WITH the canonical description as context
    all_pairs: list[tuple[str, str]] = []
    for canonical_key, description, aliases in CANONICAL_FIELDS:
        # Embed the canonical key itself with its description
        canonical_text = build_canonical_text(canonical_key, description)
        all_pairs.append((canonical_key, canonical_text))

        # Embed each alias with context
        for alias in aliases:
            enriched = f"{alias} — {description}"
            all_pairs.append((canonical_key, enriched))

    all_texts = [text for _, text in all_pairs]

    logger.info("seed_embedding", total_labels=len(all_texts))
    embeddings = await embedding_service.embed_batch(all_texts)

    if len(embeddings) != len(all_pairs):
        logger.error(
            "seed_embedding_mismatch",
            expected=len(all_pairs),
            got=len(embeddings),
        )
        return 0

    rows = []
    for (canonical_key, label_text), embedding in zip(all_pairs, embeddings):
        rows.append(
            CanonicalEmbedding(
                canonical_key=canonical_key,
                label_text=label_text,
                embedding=embedding,
                source="seed",
            )
        )

    async with db_connection.async_session_factory() as session:
        session.add_all(rows)
        await session.commit()

    logger.info(
        "seed_completed",
        canonical_keys=len(CANONICAL_FIELDS),
        total_rows=len(rows),
    )
    return len(rows)
