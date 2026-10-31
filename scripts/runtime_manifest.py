#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read the runtime catalog shared by MSBuild, native builds, CI, and .NET."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def load_runtimes(path=ROOT / "runtimes.props"):
    entries = [{"rid": item.attrib["Include"], "prefix": item.findtext("NativePrefix", ""),
                "extension": item.findtext("NativeExtension"), "os": item.findtext("Runner")}
               for item in ET.parse(path).findall(".//QualityRuntime")]
    if not entries or len({e["rid"] for e in entries}) != len(entries):
        raise ValueError("Runtime identifiers must be unique and populated.")
    if any(not e["os"] or not e["extension"] or any(c in e["rid"] + e["prefix"] + e["extension"] for c in "/\\") for e in entries):
        raise ValueError("Each runtime requires a runner and safe native filename components.")
    return entries

def native_file(entry, algorithm):
    return f'{entry["prefix"]}openphysical_{algorithm}.{entry["extension"]}'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", action="store_true", help="Emit the GitHub Actions include matrix.")
    parser.add_argument("--verify-assets", type=Path, help="Verify staged assets for both algorithms.")
    args = parser.parse_args()
    entries = load_runtimes()
    if args.verify_assets:
        for algorithm in ("nfiq1", "nfiq2"):
            for entry in entries:
                path = args.verify_assets / algorithm / entry["rid"] / "native" / native_file(entry, algorithm)
                if not path.is_file():
                    raise SystemExit(f"Missing runtime asset: {path}")
        print(f"Verified {len(entries)} runtimes for each quality algorithm.")
    else:
        print(json.dumps({"include": [{"os": e["os"], "rid": e["rid"]} for e in entries]}, separators=(",", ":")))

if __name__ == "__main__":
    main()
