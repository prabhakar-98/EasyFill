_SINGLE_SELECT = (
    "TASK: Match the user's data to EXACTLY one option from the list.\n\n"
    "RULES:\n"
    "- Return the exact option string; never modify or create options.\n"
    "- Compare the user's data against EVERY option.\n"
    "- If multiple options partially match and the correct one is unclear, "
    "return EMPTY.\n"
    "- If no specific option matches but the data is valid and \"Other\" "
    "exists, return the exact \"Other\" option.\n"
    "- If data is missing or no option matches, return EMPTY."
)

_CHECKBOX = (
    "TASK: Select ALL options that match the user's data.\n\n"
    "RULES:\n"
    "- Check EVERY option against the user's data.\n"
    "- Return all matching options as comma-separated exact strings.\n"
    "- If only one matches, return that option.\n"
    "- If no specific option matches but \"Other\" exists and the data "
    "is valid, return the exact \"Other\" option.\n"
    "- If data is missing or no option matches, return EMPTY."
)

_DATE = (
    "TASK: Extract a complete date from the user's data.\n\n"
    "RULES:\n"
    "- Return date in YYYY-MM-DD format.\n"
    "- If any part (year, month, or day) is missing or unknown, "
    "return EMPTY.\n"
    "- Never guess or assume missing date parts.\n"
    "- If the date is missing, incomplete, or unknown, return EMPTY."
)

_TIME = (
    "TASK: Extract a time from the user's data.\n\n"
    "RULES:\n"
    "- Return time in HH:MM 24-hour format (e.g. 14:30, 09:00).\n"
    "- If the time is missing, incomplete, or unknown, return EMPTY.\n"
    "- Never guess or assume a time not in the user's data."
)

_PARAGRAPH = (
    "TASK: Write a complete, well-formed response using the user's data.\n\n"
    "RULES:\n"
    "- Write in a professional, confident, and natural tone.\n"
    "- Combine relevant information from the user's profile and "
    "retrieved context.\n"
    "- Answer every part of the field's question without repeating it "
    "or adding filler.\n"
    "- Ensure every claim is supported by the user's data; never "
    "invent details.\n"
    "- If the field asks for a description, cover all requested aspects "
    "— nothing more, nothing less.\n"
    "- If asked about a specific project or experience, describe only "
    "that one; do not mix in others.\n"
    "- If the field asks about a project, include the role, technologies, "
    "tech stack, and relevant details when available and requested.\n"
    "- If the field does not ask for a description, answer directly "
    "in the expected tone and length.\n"
    "- If the user's data is insufficient for a meaningful answer, "
    "return EMPTY."
)

_SHORT_ANSWER = (
    "TASK: Write a brief, accurate response using the user's data.\n\n"
    "RULES:\n"
    "- Use a professional, natural tone.\n"
    "- Combine relevant profile data and retrieved context.\n"
    "- Answer all parts of the question without filler.\n"
    "- For project descriptions, include the purpose, role, and "
    "tech stack when available.\n"
    "- Never invent information.\n"
    "- If the data is insufficient, return EMPTY."
)

_LINEAR_SCALE = (
    "TASK: Select a rating from the scale based on the user's data.\n\n"
    "RULES:\n"
    "- Return a single integer within the scale range.\n"
    "- Base your rating on the user's actual data — do not default "
    "to the midpoint.\n"
    "- If the user's data does not support a rating, return EMPTY."
)

_GRID = (
    "TASK: Answer each row of the grid using the user's data.\n\n"
    "RULES:\n"
    "- Answer each row on its own line in the format: Row label: Option\n"
    "- Choose exactly one option per row using the exact option text.\n"
    "- If a row cannot be answered, write: Row label: EMPTY\n"
    "- Never modify or create options."
)

_SINGLE_SELECT_TYPES = frozenset({
    "dropdown", "radio", "multiple_choice", "select",
})

FIELD_TYPE_INSTRUCTIONS: dict[str, str | None] = {
    "dropdown": _SINGLE_SELECT,
    "radio": _SINGLE_SELECT,
    "multiple_choice": _SINGLE_SELECT,
    "select": _SINGLE_SELECT,
    "checkbox": _CHECKBOX,
    "date": _DATE,
    "time": _TIME,
    "long_text": _SHORT_ANSWER,
    "short_text": _SHORT_ANSWER,
    "text": _SHORT_ANSWER,
    "linear_scale": _LINEAR_SCALE,
    "grid": _GRID,
    "file_upload": None,
    "unknown": _SHORT_ANSWER,
    "other": _SHORT_ANSWER,
}


def get_field_instruction(field_type: str) -> str | None:
    """Return the type-specific prompt instruction for a field type."""
    return FIELD_TYPE_INSTRUCTIONS.get(field_type)
