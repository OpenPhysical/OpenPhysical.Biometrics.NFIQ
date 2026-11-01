#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify the curated NFIQ 1 sources, optionally against the official NBIS ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from source_provenance import verify as verify_source, original_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "native/nfiq1"


def verify(archive=None):
    hashes = json.loads((SOURCE / "upstream-sha256.json").read_text())
    origin = json.loads((SOURCE / "upstream-origin.json").read_text())
    verify_source(SOURCE)
    corrections = json.loads((SOURCE / "source-corrections.json").read_text())
    if archive is not None:
        if hashlib.sha256(archive.read_bytes()).hexdigest() != origin["archive_sha256"]:
            raise ValueError("The NBIS archive checksum differs from the pinned release.")
        with zipfile.ZipFile(archive) as release:
            for relative in hashes:
                original = origin["source_paths"].get(relative, relative)
                if release.read(origin["archive_root"] + original) != original_bytes(SOURCE, relative, corrections):
                    raise ValueError(f"Imported source differs from the NIST release: {relative}")
    print(f"Verified {len(hashes)} NFIQ 1 source receipts and their complete file inventory.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Official NBIS 5.0.0 ZIP for a byte-for-byte release comparison.")
    verify(parser.parse_args().archive)
