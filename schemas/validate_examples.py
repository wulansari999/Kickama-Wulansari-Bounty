#!/usr/bin/env python3
"""Validate schema examples for the Zeroeye JSON schema bounty.

The valid examples must pass. Files whose names start with ``invalid-``
are expected to fail validation so reviewers can see the schema reject a
representative malformed payload.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "api-error.schema.json"
EXAMPLE_DIR = ROOT / "examples" / "api-error"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    schema = cast(dict[str, Any], load_json(SCHEMA_PATH))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    results: list[tuple[str, str]] = []
    for path in sorted(EXAMPLE_DIR.glob("*.json")):
        payload = load_json(path)
        errors = sorted(validator.iter_errors(payload), key=lambda error: error.path)
        should_fail = path.name.startswith("invalid-")

        if should_fail and errors:
            results.append((path.name, "expected validation failure"))
            continue
        if should_fail and not errors:
            raise SystemExit(f"{path}: expected validation failure, but payload passed")
        if errors:
            messages = "; ".join(error.message for error in errors)
            raise SystemExit(f"{path}: unexpected validation failure: {messages}")
        results.append((path.name, "valid"))

    for name, status in results:
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
