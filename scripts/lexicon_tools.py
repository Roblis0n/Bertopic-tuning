#!/usr/bin/env python3
"""Compile and apply auditable lexical resources for BERTopic representations.

The module intentionally operates on the lexical view only. It does not mutate raw,
embedding, or display text and it does not fit or change topic assignments.
"""

from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Callable, Iterable


ACTIVE_STATUS = "active"
ALLOWED_STATUSES = {"active", "proposed", "rejected", "retired"}

TABLE_SCHEMAS = {
    "synonyms": {"canonical_term", "variant", "status", "source", "reason"},
    "stopwords": {"term", "status", "source", "reason"},
    "custom_terms": {
        "term",
        "display_form",
        "term_type",
        "status",
        "source",
        "reason",
    },
}

CANONICAL_MANIFEST_FIELDS = (
    "schema_version",
    "bundle_name",
    "parent_bundle_id",
    "apply_to",
    "normalization",
    "tokenizer",
    "synonyms",
    "stopwords",
    "custom_terms",
)


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalization_rules(config: dict[str, Any]) -> dict[str, Any]:
    raw = config.get("normalization", {})
    if not isinstance(raw, dict):
        raise ValueError("normalization must be an object")
    unicode_form = raw.get("unicode_form") or None
    if unicode_form not in {None, "NFC", "NFKC", "NFD", "NFKD"}:
        raise ValueError("normalization.unicode_form must be null, NFC, NFKC, NFD, or NFKD")
    casefold = raw.get("casefold", False)
    collapse_whitespace = raw.get("collapse_whitespace", True)
    if not isinstance(casefold, bool) or not isinstance(collapse_whitespace, bool):
        raise ValueError("normalization flags must be boolean")
    return {
        "unicode_form": unicode_form,
        "casefold": casefold,
        "collapse_whitespace": collapse_whitespace,
    }


def normalize_term(value: Any, rules: dict[str, Any]) -> str:
    """Normalize one lexical term according to the explicit bundle configuration."""
    text = str(value)
    unicode_form = rules.get("unicode_form")
    if unicode_form:
        text = unicodedata.normalize(unicode_form, text)
    if rules.get("casefold"):
        text = text.casefold()
    if rules.get("collapse_whitespace", True):
        text = " ".join(text.split())
    else:
        text = text.strip()
    return text


def validate_lexicon_manifest(bundle: dict[str, Any]) -> None:
    """Reject manifests that are not compiled, identified, lexical-only and conflict-free."""
    if not isinstance(bundle, dict):
        raise ValueError("Compiled lexicon bundle must be a JSON object")
    if bundle.get("apply_to") != "lexical_text":
        raise ValueError("Compiled lexicon bundle must apply to lexical_text")
    if not str(bundle.get("bundle_id", "")).strip():
        raise ValueError("Compiled lexicon bundle must contain bundle_id")
    if not str(bundle.get("content_sha256", "")).strip():
        raise ValueError("Compiled lexicon bundle must contain content_sha256")
    if bundle.get("conflicts") != []:
        raise ValueError("Compiled lexicon bundle contains unresolved conflicts")
    if not isinstance(bundle.get("synonym_map"), dict):
        raise ValueError("Compiled lexicon bundle must contain a synonym_map object")
    _normalization_rules(bundle)
    tokenizer = bundle.get("tokenizer")
    if not isinstance(tokenizer, dict):
        raise ValueError("Compiled lexicon bundle must identify its tokenizer")
    for field in ("name", "revision"):
        if not str(tokenizer.get(field, "")).strip():
            raise ValueError(f"Compiled lexicon bundle tokenizer.{field} must not be blank")
    for field in ("synonyms", "stopwords", "custom_terms"):
        if not isinstance(bundle.get(field), list):
            raise ValueError(f"Compiled lexicon bundle {field} must be a list")

    expected_synonym_map: dict[str, str] = {}
    for index, row in enumerate(bundle["synonyms"]):
        if not isinstance(row, dict):
            raise ValueError(f"Compiled lexicon bundle synonym {index} must be an object")
        variant = str(row.get("variant", ""))
        canonical = str(row.get("canonical_term", ""))
        if not variant or not canonical:
            raise ValueError("Compiled lexicon bundle synonyms require variant and canonical_term")
        if variant in expected_synonym_map:
            raise ValueError(f"Compiled lexicon bundle repeats synonym variant {variant!r}")
        expected_synonym_map[variant] = canonical
    if bundle["synonym_map"] != expected_synonym_map:
        raise ValueError("Compiled lexicon bundle synonym_map does not match its synonym records")

    expected_counts = {
        "synonyms": len(bundle["synonyms"]),
        "stopwords": len(bundle["stopwords"]),
        "custom_terms": len(bundle["custom_terms"]),
    }
    if bundle.get("counts") != expected_counts:
        raise ValueError("Compiled lexicon bundle counts do not match its records")

    canonical_content = {field: bundle.get(field) for field in CANONICAL_MANIFEST_FIELDS}
    canonical_bytes = json.dumps(
        canonical_content,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected_sha256 = _sha256_bytes(canonical_bytes)
    if bundle.get("content_sha256") != expected_sha256:
        raise ValueError("Compiled lexicon bundle content_sha256 does not match its content")
    if bundle.get("bundle_id") != f"lexicon-{expected_sha256[:16]}":
        raise ValueError("Compiled lexicon bundle bundle_id does not match its content hash")


def _read_table(path: Path, kind: str) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = set(reader.fieldnames or [])
            missing = sorted(TABLE_SCHEMAS[kind].difference(header))
            if missing:
                raise ValueError(f"{path.name} lacks required columns: {', '.join(missing)}")
            return [dict(row) for row in reader]
    except OSError as exc:
        raise ValueError(f"Cannot read {kind} table {path}: {exc}") from exc


def _resolve_source_path(root: Path, value: Any, kind: str) -> Path:
    raw_path = str(value or "").strip()
    if not raw_path:
        raise ValueError(f"files.{kind} must name a source table")
    relative_path = Path(raw_path)
    if relative_path.is_absolute():
        raise ValueError(
            f"files.{kind} must stay inside the lexicon bundle directory"
        )
    resolved_root = root.resolve()
    resolved_path = (resolved_root / relative_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"files.{kind} must stay inside the lexicon bundle directory"
        ) from exc
    return resolved_path


def _active_rows(
    rows: Iterable[dict[str, str]],
    *,
    kind: str,
    term_fields: tuple[str, ...],
) -> list[dict[str, str]]:
    active: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        status = str(row.get("status", "")).strip().casefold()
        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"{kind} row {index} has invalid status {row.get('status')!r}"
            )
        if status != ACTIVE_STATUS:
            continue
        for field in (*term_fields, "source", "reason"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"{kind} row {index} has blank required field '{field}'")
        normalized = {key: str(value or "").strip() for key, value in row.items()}
        normalized["status"] = ACTIVE_STATUS
        active.append(normalized)
    return active


def _resolve_synonym_map(mapping: dict[str, str]) -> dict[str, str]:
    resolved: dict[str, str] = {}

    def resolve(term: str, trail: tuple[str, ...]) -> str:
        if term not in mapping:
            return term
        if term in trail:
            cycle = " -> ".join((*trail, term))
            raise ValueError(f"Synonym mapping contains a cycle: {cycle}")
        target = mapping[term]
        final = resolve(target, (*trail, term))
        resolved[term] = final
        return final

    for variant in sorted(mapping):
        resolve(variant, ())
    return resolved


def compile_lexicon_bundle(config_path: Path | str) -> dict[str, Any]:
    """Validate editable lexicon tables and return a deterministic manifest."""
    config_path = Path(config_path)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid lexicon configuration from {config_path}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("Lexicon configuration must be a JSON object")
    if config.get("schema_version") != 1:
        raise ValueError("lexicon schema_version must be 1")
    if config.get("apply_to") != "lexical_text":
        raise ValueError("Lexicon resources must apply to lexical_text only")

    normalization = _normalization_rules(config)
    tokenizer = config.get("tokenizer")
    if not isinstance(tokenizer, dict):
        raise ValueError("tokenizer must be an object with name and revision")
    for field in ("name", "revision"):
        if not str(tokenizer.get(field, "")).strip():
            raise ValueError(f"tokenizer.{field} must not be blank")
    files = config.get("files")
    if not isinstance(files, dict):
        raise ValueError("files must map synonyms, stopwords, and custom_terms")
    missing_file_keys = sorted(set(TABLE_SCHEMAS).difference(files))
    if missing_file_keys:
        raise ValueError(f"files lacks entries: {', '.join(missing_file_keys)}")

    paths = {
        kind: _resolve_source_path(config_path.parent, files[kind], kind)
        for kind in TABLE_SCHEMAS
    }
    raw_tables = {kind: _read_table(path, kind) for kind, path in paths.items()}
    synonyms = _active_rows(
        raw_tables["synonyms"],
        kind="synonyms",
        term_fields=("canonical_term", "variant"),
    )
    stopwords = _active_rows(
        raw_tables["stopwords"], kind="stopwords", term_fields=("term",)
    )
    custom_terms = _active_rows(
        raw_tables["custom_terms"],
        kind="custom_terms",
        term_fields=("term", "display_form", "term_type"),
    )

    direct_map: dict[str, str] = {}
    synonym_records: dict[tuple[str, str], dict[str, str]] = {}
    for row in synonyms:
        canonical = normalize_term(row["canonical_term"], normalization)
        variant = normalize_term(row["variant"], normalization)
        if not canonical or not variant:
            raise ValueError("Active synonym terms must not normalize to empty strings")
        if variant == canonical:
            continue
        previous = direct_map.get(variant)
        if previous is not None and previous != canonical:
            raise ValueError(
                f"Synonym variant {variant!r} maps to multiple canonical terms: "
                f"{previous!r} and {canonical!r}"
            )
        direct_map[variant] = canonical
        record = {
            "variant": variant,
            "canonical_term": canonical,
            "source": row["source"],
            "reason": row["reason"],
        }
        existing_record = synonym_records.get((variant, canonical))
        if existing_record is not None and existing_record != record:
            raise ValueError(
                f"Synonym {variant!r} -> {canonical!r} has conflicting active records"
            )
        synonym_records[(variant, canonical)] = record
    synonym_map = _resolve_synonym_map(direct_map)

    stopword_records: dict[str, dict[str, str]] = {}
    for row in stopwords:
        term = normalize_term(row["term"], normalization)
        if not term:
            raise ValueError("Active stopwords must not normalize to empty strings")
        record = {
            "term": term,
            "source": row["source"],
            "reason": row["reason"],
        }
        existing_record = stopword_records.get(term)
        if existing_record is not None and existing_record != record:
            raise ValueError(f"Stopword {term!r} has conflicting active records")
        stopword_records[term] = record

    custom_records: dict[str, dict[str, str]] = {}
    for row in custom_terms:
        term = normalize_term(row["term"], normalization)
        display_form = str(row["display_form"]).strip()
        if not term:
            raise ValueError("Active custom terms must not normalize to empty strings")
        record = {
            "term": term,
            "display_form": display_form,
            "term_type": row["term_type"],
            "source": row["source"],
            "reason": row["reason"],
        }
        previous = custom_records.get(term)
        if previous is not None and previous != record:
            raise ValueError(f"Custom term {term!r} has conflicting active records")
        custom_records[term] = record

    stopword_set = set(stopword_records)
    custom_set = set(custom_records)
    custom_stopword_conflicts = sorted(stopword_set.intersection(custom_set))
    if custom_stopword_conflicts:
        raise ValueError(
            f"Term {custom_stopword_conflicts[0]!r} is both a stopword and a custom term"
        )
    synonym_terms = set(synonym_map).union(synonym_map.values())
    synonym_stopword_conflicts = sorted(stopword_set.intersection(synonym_terms))
    if synonym_stopword_conflicts:
        raise ValueError(
            f"Stopword {synonym_stopword_conflicts[0]!r} conflicts with an active synonym mapping"
        )

    final_synonyms = [
        {
            **synonym_records[(variant, direct_map[variant])],
            "canonical_term": synonym_map[variant],
        }
        for variant in sorted(synonym_map)
    ]
    canonical_content = {
        "schema_version": 1,
        "bundle_name": str(config.get("bundle_name", "")).strip(),
        "parent_bundle_id": str(config.get("parent_bundle_id", "")).strip(),
        "apply_to": "lexical_text",
        "normalization": normalization,
        "tokenizer": tokenizer,
        "synonyms": final_synonyms,
        "stopwords": [stopword_records[term] for term in sorted(stopword_records)],
        "custom_terms": [custom_records[term] for term in sorted(custom_records)],
    }
    canonical_bytes = json.dumps(
        canonical_content,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    content_sha256 = _sha256_bytes(canonical_bytes)
    source_files = [
        {
            "kind": kind,
            "path": paths[kind].relative_to(config_path.parent.resolve()).as_posix(),
            "sha256": _sha256_bytes(paths[kind].read_bytes()),
        }
        for kind in sorted(paths)
    ]
    return {
        **canonical_content,
        "bundle_id": f"lexicon-{content_sha256[:16]}",
        "content_sha256": content_sha256,
        "synonym_map": {key: synonym_map[key] for key in sorted(synonym_map)},
        "source_files": source_files,
        "counts": {
            "synonyms": len(final_synonyms),
            "stopwords": len(stopword_records),
            "custom_terms": len(custom_records),
        },
        "conflicts": [],
    }


def _protected_tokenize(
    text: str,
    *,
    base_tokenizer: Callable[[str], Iterable[str]],
    protected_terms: list[str],
) -> list[str]:
    if not protected_terms:
        return [str(token) for token in base_tokenizer(text)]
    tokens: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            tokens.extend(str(token) for token in base_tokenizer("".join(buffer)))
            buffer.clear()

    def matches_at(term: str, index: int) -> bool:
        if not text.startswith(term, index):
            return False
        end = index + len(term)
        if term[0].isascii() and (term[0].isalnum() or term[0] == "_"):
            if index > 0 and text[index - 1].isascii() and (
                text[index - 1].isalnum() or text[index - 1] == "_"
            ):
                return False
        if term[-1].isascii() and (term[-1].isalnum() or term[-1] == "_"):
            if end < len(text) and text[end].isascii() and (
                text[end].isalnum() or text[end] == "_"
            ):
                return False
        return True

    index = 0
    while index < len(text):
        matched = next((term for term in protected_terms if matches_at(term, index)), None)
        if matched is None:
            buffer.append(text[index])
            index += 1
            continue
        flush()
        tokens.append(matched)
        index += len(matched)
    flush()
    return tokens


def make_lexicon_tokenizer(
    base_tokenizer: Callable[[str], Iterable[str]],
    bundle: dict[str, Any],
) -> Callable[[str], list[str]]:
    """Wrap a tokenizer with phrase protection, synonym mapping, and stop filtering."""
    validate_lexicon_manifest(bundle)
    rules = bundle.get("normalization", {})
    synonym_map = {
        normalize_term(key, rules): normalize_term(value, rules)
        for key, value in dict(bundle.get("synonym_map", {})).items()
    }
    stopwords = {
        normalize_term(item["term"] if isinstance(item, dict) else item, rules)
        for item in bundle.get("stopwords", [])
    }
    custom_terms = [
        normalize_term(item["term"] if isinstance(item, dict) else item, rules)
        for item in bundle.get("custom_terms", [])
    ]
    protected_terms = sorted(
        {term for term in (*custom_terms, *synonym_map, *synonym_map.values()) if term},
        key=lambda term: (-len(term), term),
    )

    def tokenize(text: str) -> list[str]:
        lexical_text = normalize_term(text, rules)
        raw_tokens = _protected_tokenize(
            lexical_text,
            base_tokenizer=base_tokenizer,
            protected_terms=protected_terms,
        )
        result: list[str] = []
        for raw_token in raw_tokens:
            token = normalize_term(raw_token, rules)
            if not token:
                continue
            token = synonym_map.get(token, token)
            if token not in stopwords:
                result.append(token)
        return result

    return tokenize


def build_count_vectorizer(
    bundle: dict[str, Any],
    *,
    base_tokenizer: Callable[[str], Iterable[str]],
    **vectorizer_kwargs: Any,
) -> Any:
    """Build a CountVectorizer that learns corpus vocabulary after lexicon processing."""
    if "vocabulary" in vectorizer_kwargs and not bundle.get("closed_vocabulary_mode", False):
        raise ValueError(
            "A fixed vocabulary is a closed vocabulary; enable an explicit closed-vocabulary "
            "structural policy instead of treating custom terms as an allowlist"
        )
    forbidden = {"tokenizer", "token_pattern", "stop_words"}.intersection(vectorizer_kwargs)
    if forbidden:
        raise ValueError(
            "Lexicon bundles manage tokenizer, token_pattern, and stop_words; remove: "
            + ", ".join(sorted(forbidden))
        )
    try:
        from sklearn.feature_extraction.text import CountVectorizer
    except ImportError as exc:  # pragma: no cover - depends on the modeling environment
        raise RuntimeError("scikit-learn is required to build CountVectorizer") from exc
    return CountVectorizer(
        tokenizer=make_lexicon_tokenizer(base_tokenizer, bundle),
        token_pattern=None,
        stop_words=None,
        **vectorizer_kwargs,
    )
