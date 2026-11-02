#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify that NuGet preserves every staged runtime file's path and contents."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from runtime_manifest import ROOT, load_runtimes, native_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path, default=ROOT / "artifacts/packages")
    parser.add_argument("--runtimes", type=Path, default=ROOT / "artifacts/runtimes")
    args = parser.parse_args()
    version = ET.parse(ROOT / "Directory.Build.props").findtext("./PropertyGroup/Version")
    for algorithm in ("nfiq1", "nfiq2"):
        stage = args.runtimes / algorithm
        expected = {
            "runtimes/" + path.relative_to(stage).as_posix(): path
            for path in stage.rglob("*") if path.is_file()
        }
        for entry in load_runtimes():
            name = f"runtimes/{entry['rid']}/native/{native_file(entry, algorithm)}"
            if name not in expected:
                raise SystemExit(f"Missing staged runtime: {algorithm}: {name}")
        package = args.packages / f"OpenPhysical.Biometrics.{algorithm.upper()}.{version}.nupkg"
        with zipfile.ZipFile(package) as archive:
            names = [name for name in archive.namelist() if name.startswith("runtimes/")]
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise SystemExit(
                    f"{package.name}: runtime paths differ from staging. "
                    f"Missing: {sorted(set(expected) - set(names))}; "
                    f"unexpected: {sorted(set(names) - set(expected))}"
                )
            for name, source in expected.items():
                if archive.read(name) != source.read_bytes():
                    raise SystemExit(f"{package.name}: runtime contents differ: {name}")
        print(f"Verified {package.name}: {len(expected)} runtime files, exact paths and contents.")


if __name__ == "__main__":
    main()
