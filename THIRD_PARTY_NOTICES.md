# Third-party notices and corresponding source

NFIQ1 uses original NIST NBIS 5.0.0 public-domain sources. Its complete notice is
[native/nfiq1/NOTICE.txt](native/nfiq1/NOTICE.txt).

NFIQ2 v2.3.0 original licensing is retained in
[native/nfiq2/upstream/LICENSE.md](native/nfiq2/upstream/LICENSE.md).
FingerJetFX OSE is LGPL-3.0-or-later; OpenCV is Apache 2.0; digestpp is public domain.
Their complete notices and source are retained in the recursively pinned upstream
repository. NFIQ2 binary packages include those notices. Copyrights and notices
for bundled OpenCV dependencies remain in the pinned OpenCV source tree.

The matching corresponding source is this repository at the package release tag,
including its recursively pinned submodules. Clone with `--recurse-submodules` and
run `python scripts/build-native.py --algorithm nfiq2` on the relevant native runner.
This rebuilds FingerJet as a separate shared library. Replace the packaged FRFXLL
shared library with an ABI-compatible rebuilt version in the runtime native
folder; the wrapper dynamically links it. Applications distributing these assets
must retain the applicable licenses, notices and corresponding-source access.
Commercial licensing of first-party code leaves these dependency terms intact.

The SD04 fixture notice is retained separately in tests/fixtures/NIST-DATA-NOTICE.txt.

Windows NFIQ2 builds bundle the MinGW GCC C++ and pthread runtime DLLs from the
selected UCRT64 toolchain. Their accompanying GCC Runtime Library Exception and
other runtime notices are copied from that toolchain's share/licenses directory
into the native runtime license folder. Runtime compiler versions are part of
the platform build environment and should be recorded for each published release.

## NIST NFIQ2 release example images

The five SFinGe grayscale fixtures preserve pixels from the example images
shipped with NIST NFIQ2 2.3.0. Their published expected scores and source hashes
are recorded in `tests/fixtures/nfiq2-release-vectors.json`. They retain the
upstream release's applicable notices and terms, available in
`native/nfiq2/upstream/LICENSE.md` and its `examples` directory.

The release examples credit: Cappelli, R., Maio, D., and Maltoni, D.,
*SFinGe: An Approach to Synthetic Fingerprint Generation*, International
Workshop on Biometric Technologies, 2004.

The eight `a011` grayscale fixtures originate in NIST's NBIS 5.0.0 test release.
Their original WSQ files, published NFIQ expectations, decoding command and
checksums are identified in `tests/fixtures/nfiq1-release-vectors.json`. The
original NIST notices and data terms apply separately from this project's GPL.
