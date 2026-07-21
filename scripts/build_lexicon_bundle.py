#!/usr/bin/env python3
"""Validate editable lexicon tables and write a deterministic bundle manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lexicon_tools import compile_lexicon_bundle


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile synonym, stopword, and custom-term tables for BERTopic representation updates."
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = compile_lexicon_bundle(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote lexicon bundle {manifest['bundle_id']}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
