#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run the complete native suite with GCC coverage in an isolated test build."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALGORITHMS = ["nfiq1", "nfiq2"]
REPORT = ROOT / "artifacts/coverage"
REPORT.mkdir(parents=True, exist_ok=True)
for algorithm in ALGORITHMS:
    build = ROOT / "artifacts/native/coverage" / algorithm
    subprocess.run(["cmake", "-S", str(ROOT / "native" / algorithm), "-B", str(build), "-DCMAKE_C_COMPILER=gcc", "-DCMAKE_CXX_COMPILER=g++", "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_TESTING=ON", "-DCMAKE_C_FLAGS=--coverage", "-DCMAKE_CXX_FLAGS=--coverage", "-DCMAKE_SHARED_LINKER_FLAGS=--coverage", "-DCMAKE_EXE_LINKER_FLAGS=--coverage"], check=True)
    subprocess.run(["cmake", "--build", str(build), "--parallel", "4"], check=True)
    for path in build.rglob("*.gcda"):
        path.unlink()
    subprocess.run(["ctest", "--test-dir", str(build), "--output-on-failure"], check=True)
    counts = sorted((build / ("CMakeFiles/openphysical_" + algorithm + ".dir")).rglob("*.gcda"))
    if not counts:
        raise SystemExit("The native suite produced no coverage counters: " + algorithm)
    destination = REPORT / algorithm
    destination.mkdir(exist_ok=True)
    for path in counts:
        subprocess.run(["gcov", "--branch-probabilities", "--branch-counts", "--json-format", str(path)], cwd=destination, check=True)
print("Native coverage reports captured.")
