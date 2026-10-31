#!/usr/bin/env python3
"""Build independent tools from original algorithm sources, outside the wrapper."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--build-directory", type=Path, required=True)
args = parser.parse_args()
build = args.build_directory.resolve()
build.mkdir(parents=True, exist_ok=True)
source = build / "source"
source.mkdir(exist_ok=True)
# These are separate targets: no wrapper source, allocation interception, or
# generated safety adaptations enter the reference build.
s = (ROOT / "native/nfiq2/CMakeLists.txt").read_text()
s = s[:s.rindex("include(CTest)")]
a = s.index("# Test builds inject")
b = s.index("add_library(openphysical_nfiq2", a)
s = s[:a] + s[b:]
a = s.index("# Keep typed statistical kernels")
b = s.index('set(FRFXLL_PATH', a)
s = s[:a] + s[b:]
a = s.index("# The third-order")
b = s.index("# Build FingerJet", a)
s = s[:a] + s[b:]
a = s.index("# Base64 decoding")
b = s.index("set(NFIQ2_VERSION_MAJOR", a)
s = s[:a] + s[b:]
s = s.replace('set(U "${CMAKE_CURRENT_SOURCE_DIR}/upstream")', 'set(U "' + str(ROOT / "native/nfiq2/upstream") + '")')
s = s.replace('SHARED op_nfiq2.cpp ${NFIQ_SOURCES}', 'SHARED ${NFIQ_SOURCES}')
s = s[:s.index('set_source_files_properties(op_nfiq2.cpp')]
s = s.replace('target_include_directories(openphysical_nfiq2 BEFORE PRIVATE "${OPENCV_OVERLAY}")', '')
s += '\nadd_executable(nfiq2_reference "' + str(ROOT / "tests/native/nfiq2_reference.cpp") + '")\n'
s += 'target_include_directories(nfiq2_reference PRIVATE "${A}/include")\ntarget_link_libraries(nfiq2_reference PRIVATE openphysical_nfiq2)\n'
(source / "CMakeLists.txt").write_text(s)
subprocess.run(["cmake", "-S", str(source), "-B", str(build / "build"), "-DCMAKE_BUILD_TYPE=Release"], check=True)
subprocess.run(["cmake", "--build", str(build / "build"), "--target", "nfiq2_reference", "--parallel", str(min(os.cpu_count() or 2, 8))], check=True)
print("Independent original-source NFIQ2 reference tool:", build / "build/bin/nfiq2_reference")
