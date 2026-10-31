#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Vendor the allocator from an explicitly selected NBIS source checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--nbis-source", type=Path, required=True)
options = parser.parse_args()
receipt = {"source_repository": "https://github.com/OpenPhysical/OpenPhysical.Biometrics.NBIS",
           "source_directory": "native/nbis", "license": "GPL-2.0-or-later", "files": {}}
for name in ("op_alloc.c", "op_alloc.h"):
    source = options.nbis_source / "native/nbis" / name
    data = source.read_bytes()
    shutil.copyfile(source, ROOT / "native/nfiq1" / name)
    # Git blob IDs identify the exact canonical files independently of commit amendments.
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    receipt["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(), "git_blob": blob}
(ROOT / "native/nfiq1/allocator-provenance.json").write_text(json.dumps(receipt, indent=2) + "\n")
print("Updated the vendored allocator and immutable source-file receipts.")
