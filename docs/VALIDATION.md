# Validation record

The initial local validation ran on macOS ARM64 with .NET 10 and Apple Clang.

* Both managed libraries build with zero warnings and errors; NUnit binding tests pass.
* Public documentation gate accepts documented APIs and rejects missing summaries,
  parameters, return descriptions, invalid references and disabled/downgraded gates.
* Original NFIQ native tests cover independent reference values, blank images,
  malformed inputs and recovery after allocation failures at six different depths.
* NFIQ2 native tests cover the pinned model, malformed input and reference scores.
* Both native suites pass ASan and halting UBSan with their final adaptations.
* A temporary application outside this repository consumes both NuGet packages,
  assesses the real SD04 capture and verifies missing-native-library failures.
* Package checks exclude fixture images and retain dependency license files.

The NFIQ1 reference executable links the independently built, unmodified NBIS
5.0.0 libraries. The NFIQ2 reference executable is independently built from original algorithm
and dependency sources, with no wrapper or generated-source adaptations. It
reproduces all five expected example scores shipped by NIST in NFIQ2 2.3.0.
Eight NBIS release captures reproduce the published classes/confidences, and
representative release vectors verify both managed bindings.
Twenty SD04 impressions are assessed by the official NBIS CLI and the independent
reference tools. Both reference programs, reproduction scripts and fixture provenance are committed.
The model hash and baseline scores remain unchanged after the adaptations.

CI defines native builds, managed tests, sanitizer checks and complete-package
consumption on every runtime in [runtimes.props](../runtimes.props). Runtime packages
for local validation contain the current host's assets. Published releases collect
and validate all five runtime builds through the complete-package matrix.

The upstream sources remain unmodified. Native adaptation details and exact
source/dependency pins are recorded in native/PROVENANCE.md and upstream locks.
