#!/usr/bin/env python3
"""Audit the shared IntegerMigrator filename sequence without loading Ruby/Sequel.

Python 3.9+, standard library only. Not for Local's timestamp migrations. This
checks filenames, not SQL validity, reversibility, adapter behavior or data safety.
"""
import argparse
import json
from pathlib import Path
import re

PATTERN = re.compile(r"([0-9]{3,})_[a-zA-Z0-9_]+\.rb\Z")


def audit(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError("migration directory does not exist")
    versions, errors = {}, []
    for path in sorted(directory.iterdir()):
        if path.suffix != ".rb":
            continue
        if path.is_symlink() or not path.is_file():
            errors.append(f"not a regular migration file: {path.name}")
            continue
        match = PATTERN.fullmatch(path.name)
        if not match:
            errors.append(f"invalid migration filename: {path.name}")
            continue
        version = int(match.group(1))
        if version < 1:
            errors.append(f"migration version must be positive: {path.name}")
            continue
        versions.setdefault(version, []).append(path.name)
    for version, names in sorted(versions.items()):
        if len(names) > 1:
            errors.append(f"duplicate migration version {version}: {', '.join(names)}")
    ordered = sorted(versions)
    # Compare adjacent IDs rather than allocating a range controlled by filenames.
    previous = 0
    for version in ordered:
        if version != previous + 1:
            errors.append(f"missing migration versions {previous + 1}..{version - 1}")
        previous = version
    if not ordered:
        errors.append("no numbered migrations found")
    return {"count": sum(map(len, versions.values())), "latest_version": ordered[-1] if ordered else None,
            "next_version": ordered[-1] + 1 if ordered and not errors else None,
            "errors": errors, "database_accessed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path,
                        default=Path(__file__).resolve().parents[1] / "lib/legion/data/migrations")
    args = parser.parse_args()
    try:
        result = audit(args.directory)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return bool(result["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
