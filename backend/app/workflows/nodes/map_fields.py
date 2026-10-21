from app.logging import get_logger
from app.workflows.events import emit_event
from app.services.embedding import embedding_service
from app.services.seed_canonical import ALIAS_MAP
from app.workflows.state import FieldInput, MappedField, WorkflowState

logger = get_logger("workflow.map_fields")

# Top-k acceptance thresholds
VECTOR_TOP_K = 5
HIGH_CONFIDENCE = 0.92
MEDIUM_CONFIDENCE = 0.75
MIN_GAP = 0.05


def _normalize_label(label: str) -> str:
    return " ".join(label.lower().strip().split())


def _try_alias_match(label: str) -> str | None:
    """Tier 1: Deterministic alias lookup — zero cost."""
    normalized = _normalize_label(label)
    return ALIAS_MAP.get(normalized)


def _deduplicate_candidates(candidates: list[dict]) -> list[dict]:
    """Keep only the highest-similarity entry per canonical_key."""
    seen: dict[str, dict] = {}
    for c in candidates:
        key = c["canonical_key"]
        if key not in seen or c["similarity"] > seen[key]["similarity"]:
            seen[key] = c
    return sorted(seen.values(), key=lambda x: x["similarity"], reverse=True)


def _validate_candidates(candidates: list[dict]) -> dict | None:
    """Tier 2: Top-k acceptance checks.

    Returns the accepted candidate dict or None if ambiguous.
    """
    if not candidates:
        return None

    best = candidates[0]
    similarity = best["similarity"]

    # Below medium confidence — no match
    if similarity < MEDIUM_CONFIDENCE:
        return None

    # High confidence with clear gap — accept
    if similarity >= HIGH_CONFIDENCE:
        if len(candidates) < 2:
            return best
        gap = similarity - candidates[1]["similarity"]
        if gap >= MIN_GAP:
            return best
        # High similarity but close competitor — ambiguous
        return None

    # Medium range (0.75–0.92) — only accept if large gap
    if len(candidates) >= 2:
        gap = similarity - candidates[1]["similarity"]
        if gap >= MIN_GAP * 2:
            return best

    return None


# async def _try_llm_mapping(
#     label: str,
#     description: str | None,
#     candidates: list[dict] | None = None,
#     task_id: str = "",
#     workflow_id: str = "",
# ) -> str | None:
#     """Tier 3: LLM fallback — only for ambiguous/unresolved cases."""
#     prompt = build_field_mapping_prompt(label, description, ALL_CANONICAL_KEYS)
#
#     # Add top candidates as hints if available
#     if candidates:
#         hint_lines = [f"  - {c['canonical_key']} (similarity: {c['similarity']:.2f})" for c in candidates[:3]]
#         prompt += "\n\nTop vector candidates:\n" + "\n".join(hint_lines)
#
#     try:
#         response = await tracked_generate(
#             ModelRequest(
#                 messages=[
#                     Message(role="system", content=FIELD_MAPPING_SYSTEM_PROMPT),
#                     Message(role="user", content=prompt),
#                 ],
#                 task_type="field_mapping",
#             ),
#             task_id=task_id,
#             workflow_id=workflow_id,
#             agent_type="field_mapping",
#         )
#         result = response.content.strip().lower()
#
#         # Validate: must be an existing canonical key
#         if result in ALL_CANONICAL_KEYS:
#             return result
#         if result == "unknown":
#             return None
#         for key in ALL_CANONICAL_KEYS:
#             if key in result:
#                 return key
#         return None
#     except Exception as e:
#         logger.warning("llm_mapping_failed", label=label, error=str(e))
#         return None


async def map_fields_node(state: WorkflowState) -> dict:
    fields: list[FieldInput] = state["fields"]
    mapped: list[MappedField] = []

    alias_indices: set[int] = set()
    skipped_indices: set[int] = set()
    need_vector_fields: list[tuple[int, FieldInput]] = []

    # Skip unsupported field types
    for i, field in enumerate(fields):
        if field["type"] == "unknown":
            skipped_indices.add(i)
            mapped.append(_build_mapped(field, None, 0.0, "skipped", None))

    # Tier 1: Alias matching (deterministic, zero cost)
    for i, field in enumerate(fields):
        if i in skipped_indices:
            continue
        canonical = _try_alias_match(field["label"])
        if canonical:
            alias_indices.add(i)
            mapped.append(_build_mapped(field, canonical, 1.0, "alias", None))

    # Collect fields that need vector search
    for i, field in enumerate(fields):
        if i not in alias_indices and i not in skipped_indices:
            need_vector_fields.append((i, field))

    # Tier 2: Batch embed + top-k vector search with acceptance checks
    embeddings: list[list[float]] = []
    vector_resolved: dict[int, MappedField] = {}

    if need_vector_fields:
        labels = [f["label"] for _, f in need_vector_fields]
        embeddings = await embedding_service.embed_batch(labels)

        for (orig_idx, field), embedding in zip(need_vector_fields, embeddings):
            raw_candidates = await embedding_service.search_canonical(
                embedding, threshold=MEDIUM_CONFIDENCE, limit=VECTOR_TOP_K
            )
            # Deduplicate: keep highest similarity per canonical_key
            candidates = _deduplicate_candidates(raw_candidates)

            accepted = _validate_candidates(candidates)
            if accepted:
                vector_resolved[orig_idx] = _build_mapped(
                    field,
                    accepted["canonical_key"],
                    accepted["similarity"],
                    "vector",
                    embedding,
                )
            else:
                vector_resolved[orig_idx] = _build_mapped(
                    field, None, 0.0, "unmapped", embedding
                )

    # Merge vector/llm results
    for orig_idx, field in need_vector_fields:
        if orig_idx in vector_resolved:
            mapped.append(vector_resolved[orig_idx])

    # Sort by original index to maintain field order
    mapped.sort(key=lambda m: m["index"])

    counts = {"alias": 0, "vector": 0, "llm": 0, "unmapped": 0}
    for m in mapped:
        src = m["mapping_source"]
        if src in counts:
            counts[src] += 1

    logger.info(
        "fields_mapped",
        total=len(mapped),
        **counts,
        details=[
            {
                "label": m["label"],
                "canonical_key": m["canonical_key"],
                "confidence": m["mapping_confidence"],
                "source": m["mapping_source"],
            }
            for m in mapped
        ],
    )

    await emit_event(
        workflow_id=state.get("workflow_id", ""),
        task_id=state.get("task_id", ""),
        event_type="fields_mapped",
        data={**counts, "total": len(mapped)},
    )

    return {
        "mapped_fields": mapped,
        "status": "MAPPING_FIELDS",
        "current_node": "map_fields",
        "events": [{"type": "fields_mapped", **counts, "total": len(mapped)}],
    }


def _build_mapped(
    field: FieldInput,
    canonical_key: str | None,
    confidence: float,
    source: str,
    embedding: list[float] | None,
) -> MappedField:
    return MappedField(
        index=field["index"],
        label=field["label"],
        type=field["type"],
        required=field.get("required", False),
        description=field.get("description"),
        options=field.get("options") or [],
        canonical_key=canonical_key,
        mapping_confidence=confidence,
        mapping_source=source,
        field_embedding=embedding,
        validation=field.get("validation"),
    )
