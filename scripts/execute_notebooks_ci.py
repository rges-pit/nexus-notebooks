#!/usr/bin/env python3
"""Execute one or more Jupyter notebooks for CI.

Supports skipping cells by tag so you can have a fast CI profile (skip expensive
cells) and a full CI profile (run everything).

Usage examples:
  python scripts/execute_notebooks_ci.py --glob "notebooks/*.ipynb" --skip-tags slow,ci-skip
  python scripts/execute_notebooks_ci.py --glob "notebooks/*.ipynb" --timeout 1800
"""

from __future__ import annotations

import argparse
import glob
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import nbformat
    from nbclient import NotebookClient
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies. Install with: pip install nbclient nbformat"
    ) from exc


@dataclass(frozen=True)
class RunResult:
    path: Path
    seconds: float


def _parse_tags(value: str) -> set[str]:
    if not value:
        return set()
    return {t.strip() for t in value.split(",") if t.strip()}


def _iter_notebooks(globs: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in globs:
        paths.extend(Path(p).resolve() for p in glob.glob(pattern))
    # De-dupe while preserving order
    seen: set[Path] = set()
    ordered: list[Path] = []
    for p in paths:
        if p in seen:
            continue
        if p.is_file() and p.suffix == ".ipynb":
            seen.add(p)
            ordered.append(p)
    return ordered


def _filter_cells_by_tag(nb: dict, skip_tags: set[str]) -> tuple[dict, int]:
    if not skip_tags:
        return nb, 0

    cells = nb.get("cells", [])
    kept = []
    skipped = 0

    for cell in cells:
        meta = cell.get("metadata", {}) or {}
        tags = set(meta.get("tags", []) or [])
        if tags.intersection(skip_tags):
            skipped += 1
            continue
        kept.append(cell)

    nb["cells"] = kept
    return nb, skipped


def execute_notebook(path: Path, *, skip_tags: set[str], timeout: int, kernel_name: str) -> RunResult:
    start = time.time()
    nb = nbformat.read(str(path), as_version=4)
    nb, skipped = _filter_cells_by_tag(nb, skip_tags)

    if skipped:
        print(f"[ci] {path.name}: skipped {skipped} tagged cell(s)")

    client = NotebookClient(nb, timeout=timeout, kernel_name=kernel_name)
    client.execute()
    return RunResult(path=path, seconds=(time.time() - start))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Execute notebooks (with optional tag-based skipping).")
    parser.add_argument(
        "--glob",
        action="append",
        dest="globs",
        required=True,
        help="Glob pattern(s) to select notebooks, e.g. 'notebooks/*.ipynb'. Can be repeated.",
    )
    parser.add_argument(
        "--skip-tags",
        default="",
        help="Comma-separated cell tags to skip (e.g. 'slow,ci-skip').",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Per-notebook execution timeout in seconds (default: 900).",
    )
    parser.add_argument(
        "--kernel-name",
        default="python3",
        help="Jupyter kernel name to use (default: python3).",
    )
    args = parser.parse_args(argv)

    skip_tags = _parse_tags(args.skip_tags)
    notebooks = _iter_notebooks(args.globs)
    if not notebooks:
        raise SystemExit(f"No notebooks matched: {args.globs}")

    results: list[RunResult] = []
    for nb_path in notebooks:
        print(f"[ci] executing: {nb_path}")
        results.append(
            execute_notebook(
                nb_path,
                skip_tags=skip_tags,
                timeout=args.timeout,
                kernel_name=args.kernel_name,
            )
        )

    total = sum(r.seconds for r in results)
    print("\n[ci] summary")
    for r in results:
        print(f"- {r.path.name}: {r.seconds:.1f}s")
    print(f"[ci] total: {total:.1f}s")


if __name__ == "__main__":
    main()
