#!/usr/bin/env python3
"""Upload the 28 verified ES Minute Last files to GitHub using normal Git.

Run from the local clone of rgentil2/MES-Trading-Research:
    python tools/upload_es_minute_last.py "C:/path/to/MINUTE LAST.zip"

The script preserves file bytes, excludes the stale duplicate ES 12-26.Last.txt,
normalizes destination names, verifies SHA-256 against the tracked manifest,
and commits/pushes one contract at a time.
"""
from __future__ import annotations
import csv, hashlib, os, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data_es_staging" / "manifests" / "ES_MINUTE_LAST_MANIFEST.csv"
DEST_ROOT = ROOT / "data_es_staging" / "raw_minutes"

def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/upload_es_minute_last.py <MINUTE LAST.zip>")
    zip_path = Path(sys.argv[1]).expanduser().resolve()
    if not zip_path.exists():
        raise SystemExit(f"ZIP not found: {zip_path}")

    with MANIFEST.open(newline="", encoding="utf-8") as f:
        expected = list(csv.DictReader(f))
    if len(expected) != 28:
        raise SystemExit(f"Expected 28 manifest rows, found {len(expected)}")

    by_source = {r["source_filename"]: r for r in expected}
    with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(zip_path) as z:
        tmp = Path(td)
        names = {Path(n).name: n for n in z.namelist() if n.lower().endswith(".txt")}
        missing = [name for name in by_source if name not in names]
        if missing:
            raise SystemExit("Missing expected files: " + ", ".join(missing))

        # Deliberately ignore stale duplicate ES 12-26.Last.txt.
        for row in expected:
            src_name = row["source_filename"]
            contract = row["contract"]
            mm, yy = re.fullmatch(r"ES (03|06|09|12)-(\d{2})", contract).groups()
            mon = {"03":"MAR","06":"JUN","09":"SEP","12":"DEC"}[mm]
            contract_dir = DEST_ROOT / f"ES_{mon}{yy}"
            contract_dir.mkdir(parents=True, exist_ok=True)
            dest = contract_dir / row["repo_filename"]

            with z.open(names[src_name]) as src, dest.open("wb") as out:
                shutil.copyfileobj(src, out)

            actual = sha256(dest)
            if actual != row["sha256"]:
                dest.unlink(missing_ok=True)
                raise SystemExit(f"SHA-256 mismatch for {src_name}: {actual}")

            if dest.stat().st_size >= 100 * 1024 * 1024:
                raise SystemExit(f"Unexpected >100 MiB Minute file: {dest}")

            run("git", "add", str(dest), str(MANIFEST))
            status = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=ROOT,
            ).returncode
            if status == 0:
                print(f"{contract}: already committed, skipping")
                continue
            run("git", "commit", "-m", f"Add {contract} Minute Last raw data")
            run("git", "push")
            print(f"{contract}: uploaded and verified")

    run("git", "status", "--short")
    print("Finished: 28/28 verified Minute Last contracts processed.")

if __name__ == "__main__":
    main()
