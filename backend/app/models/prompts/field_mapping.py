FIELD_MAPPING_SYSTEM_PROMPT = (
    "You are a form field classifier. "
    "Given a form field label (and optionally a description), "
    "map it to exactly ONE canonical key from the provided list.\n\n"
    "Rules:\n"
    "- Respond with ONLY the canonical key, nothing else.\n"
    "- If no canonical key is a reasonable match, respond with UNKNOWN.\n"
    "- Do not invent new keys.\n"
    "- Consider synonyms and paraphrases when matching."
)


def build_field_mapping_prompt(
    label: str,
    description: str | None,
    candidates: list[str],
) -> str:
    parts = [f"Form field label: \"{label}\""]
    if description:
        parts.append(f"Description: \"{description}\"")
    parts.append(f"\nCanonical keys:\n{', '.join(candidates)}")
    parts.append("\nWhich canonical key does this field map to?")
    return "\n".join(parts)
