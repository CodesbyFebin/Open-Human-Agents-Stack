#!/usr/bin/env python3
"""Fetch selected permissively licensed upstreams into an isolated local vendor area.

This does not merge code into OpenMinds or grant rights beyond upstream licenses.
No upstream is fetched by default. Requires explicit --include flags.
"""
import argparse
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "integrations" / "upstreams.json"
ALLOWED = {"source-eligible"}

def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include", action="append", default=[], metavar="ID",
                        help="Explicit upstream ID to fetch; repeat for multiple projects")
    parser.add_argument("--destination", type=Path, default=ROOT / "upstreams")
    parser.add_argument("--archive", type=Path, help="Optional output ZIP path")
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    mapping = {x["id"]: x for x in registry["upstreams"]}
    requested = list(dict.fromkeys(args.include))
    if not requested:
        parser.error("Specify at least one --include ID; no bulk fetch is implicit")
    for name in requested:
        if name not in mapping:
            parser.error(f"Unknown upstream: {name}")
        if mapping[name]["mode"] not in ALLOWED:
            parser.error(f"{name} has integration mode {mapping[name]['mode']}; source import denied")
    destination = args.destination.resolve()
    if destination == ROOT or ROOT in destination.parents and destination.name == ".git":
        parser.error("Invalid destination")
    if args.archive and args.archive.resolve().is_relative_to(destination):
        parser.error("Place the archive outside the fetched source tree")
    destination.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name in requested:
        item = mapping[name]
        target = destination / name
        if target.exists():
            parser.error(f"Destination already exists, refusing to overwrite: {target}")
        run("git", "clone", "--depth", "1", "--filter=blob:none", "--",
            item["url"] + ".git", str(target))
        sha = run("git", "rev-parse", "HEAD", cwd=target)
        receipts.append({"id": name, "repository": item["repository"],
                         "commit": sha, "license": item["license"]})
        print(f"Fetched {name} at {sha}")
    receipt_path = destination / "IMPORT_RECEIPT.json"
    if receipt_path.exists():
        parser.error("Receipt already exists; refusing to overwrite")
    receipt_path.write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    if args.archive:
        archive = args.archive.resolve()
        if archive.exists():
            parser.error(f"Archive exists, refusing to overwrite: {archive}")
        archive.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(archive, "x", ZIP_DEFLATED, compresslevel=6) as z:
            for file in destination.rglob("*"):
                if not file.is_file() or ".git" in file.relative_to(destination).parts:
                    continue
                z.write(file, file.relative_to(destination.parent))
        print(f"Archive created: {archive}")
    print("Upstreams remain separately licensed. No services were deployed or verified.")

if __name__ == "__main__":
    main()
