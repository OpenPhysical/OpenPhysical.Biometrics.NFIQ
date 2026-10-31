#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify the curated NFIQ 1 sources, optionally against the official NBIS ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native/nfiq1"


def verify(archive=None):
    hashes = json.loads((SOURCE / "upstream-sha256.json").read_text())
    origin = json.loads((SOURCE / "upstream-origin.json").read_text())
    actual = {path.relative_to(SOURCE / "upstream").as_posix()
              for path in (SOURCE / "upstream").rglob("*") if path.is_file()}
    if actual != set(hashes):
        raise ValueError("Imported files differ from the authoritative source manifest.")
    for relative, wanted in hashes.items():
        if hashlib.sha256((SOURCE / "upstream" / relative).read_bytes()).hexdigest() != wanted:
            raise ValueError(f"Imported source checksum differs: {relative}")
    if archive is not None:
        if hashlib.sha256(archive.read_bytes()).hexdigest() != origin["archive_sha256"]:
            raise ValueError("The NBIS archive checksum differs from the pinned release.")
        with zipfile.ZipFile(archive) as release:
            for relative in hashes:
                original = origin["source_paths"].get(relative, relative)
                if release.read(origin["archive_root"] + original) != (SOURCE / "upstream" / relative).read_bytes():
                    raise ValueError(f"Imported source differs from the NIST release: {relative}")
    print(f"Verified {len(hashes)} original NFIQ 1 source files and their complete file inventory.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Official NBIS 5.0.0 ZIP for a byte-for-byte release comparison.")
    verify(parser.parse_args().archive)
