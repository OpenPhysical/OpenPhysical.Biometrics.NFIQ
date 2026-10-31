# Upstream source provenance

NFIQ1 sources are byte-preserving copies from the official NIST NBIS 5.0.0 archive,
SHA-256 `0adf8ab0f6b0e4208de50ca00ba21d3d77112ecd66288757ddfed21f6bee92c3`.
The complete imported-file hashes are in `nfiq1/upstream-sha256.json`.
`nfiq1/upstream-origin.json` records the archive prefix and the one unchanged
header copied from `imgtools/include/swap.h` into the selected include closure.
The generated `pcasys/include/little.h` is excluded; its original `.src` template
is retained. `scripts/verify-nfiq1-source.py --archive /path/to/nbis_v5_0_0.zip`
compares every selected file directly with the pinned official archive. Normal
builds verify both the file inventory and its hashes offline.
Source: https://www.nist.gov/services-resources/software/nist-biometric-image-software-nbis

NFIQ2 is pinned to official release v2.3.0, commit
`76b8c4e0b0541f3deab832b1a496e524edc0b5b6`, with its upstream submodule pins.
Source: https://github.com/usnistgov/NFIQ2/tree/v2.3.0
The original vendor trees are imported before adaptation or wrapper code.

## Native adaptations

NFIQ1 uses only the in-memory quality path and required MINDTCT/MLP/CBLAS
closure. A forced-include allocation arena tracks and clears all per-call memory,
unwinds allocation failures across C frames, suppresses legacy diagnostic output,
and serializes global state. Allocation and reallocation fixes from the NBIS
embedding are applied to generated build files, leaving originals untouched.
Legacy process termination becomes a controlled arena unwind.

The allocator is vendored byte-for-byte from the canonical OpenPhysical NBIS
wrapper, rather than maintained as a second implementation. Its source repository,
Git blob identifiers, SHA-256 receipts, and license are recorded in
`nfiq1/allocator-provenance.json`. CMake rejects a changed copy. Update both files
and their receipts with `scripts/update-allocator.py --nbis-source /path/to/NBIS`.
The release arena always unwinds failed allocations; generated minutia return
codes -430/-431/-432 are defensive fallbacks that remain unreachable with this
allocator. Test-only counters measure real allocation attempts and arena cleanup;
release builds omit those hooks.

NFIQ2 builds its original algorithm and embedded model with pinned OpenCV 4.10.0,
FingerJet d67f329511d65c94d74adacb0678680723d04094 and digestpp
873b5bbab87a8a62ea7bf2ea8d26733181a2fe8d. The wrapper catches C++ exceptions,
serializes its reusable context, and links replaceable shared dependencies.
Version metadata uses the upstream release date rather than the current clock.
The optical/ink model metadata MD5 is b4a1e7586b3be906f9770e4b77768038.

NFIQ2's Base64 decoder accumulates model bits with an unsigned integer in the
generated build source. The original signed accumulator overflowed during a left
shift (confirmed by halting UBSan on embedded-model initialization). This
adaptation preserves the decoded model hash and recorded fixture scores. The
configuration fails if the original adaptation pattern changes. Sanitizer builds
set UBSan to halt on the first diagnostic so recovered faults cannot pass silently.

FingerJet's fixed-point FFT shifts negative signed values. The standalone
FingerJet shared-library target uses C++20, which defines this two's-complement
left-shift arithmetic modulo the value width. The original C++11 configuration
triggered halting UBSan in complex.h:76. Other NFIQ2 translation units retain
C++11 for their original API compatibility. No sanitizer checks are disabled.

FingerJet's unused third-order orientation expression computes overflowing signed
intermediates even though its contribution is multiplied by constant k3=0. The
generated FingerJet build copy initializes that dead contribution to zero. The
configuration checks both the exact original expression and the zero weight before
adapting it. Active orientation terms and the original pinned sources are retained.

The generated FingerJet extraction header uses a signed row-stride offset for
`p[-3*width]`. The original unsigned width converted the negative offset into
an overflowing pointer addition. Width is bounded by the C interface, so casting
the width to int32 before multiplying preserves the intended backward access.

OpenCV flood fill now skips neighbor rows outside the image before constructing
their pixel pointers. Upstream relied on mask-border values to prevent accessing
these rows, but first formed an overflowing unsigned pointer offset. A generated
copy of floodfill.cpp adds the row-bound guard; original OpenCV source remains
unchanged. Valid pixel-neighbor processing is preserved.

Windows builds generate copies of both `mytime.h` and `util.h` that include
standard `time.h` in place of POSIX `sys/times.h`. The selected sources need
`clock_t` declarations; upstream timing instrumentation remains disabled.
NFIQ2 status 5 identifies unexpected dependency/native exceptions, separately
from status 3 carrying an original NFIQ2 assessment error code.

OpenCV's NEON `v_add_wrap(v_int16x8, v_int16x8)` expresses intentional signed
lane wrapping through a GCC intrinsic that triggers signed-overflow UBSan on
Linux ARM64. A generated header overlay performs the same addition as unsigned
16-bit lanes and reinterprets the resulting bits as signed lanes. All builds use
the same adaptation; sanitizer instrumentation remains enabled.

OpenCV's statistical dispatch originally casts typed sum/squared-sum functions
to incompatible generic buffer function pointers. Generated mean/sum headers
now give all fourteen dispatch wrappers the exact generic pointer signature and
cast buffers inside the wrapper before invoking the unchanged numerical kernel.
The casts on the dispatch table are removed, so the compiler checks every entry.
Baseline and CPU-dispatched translation units use the same generated headers.
Generated include paths use CMake-style forward slashes on every platform, and
configuration fails if an expected CPU-dispatch include cannot be redirected.
The same generated-copy approach replaces all 74 arithmetic/comparison HAL
casts with exact-signature adapters, plus the integer-power and square-root
dispatch tables. Merge/split, norm, min/max, DFT and DCT dispatch use the same
exact-signature adaptation. Numerical kernels receive the original typed pointers inside
each adapter. This resolves Clang's function-type UBSan failures on macOS x64
without excluding function-call instrumentation.

Test builds generate a copy of `nfiq2_algorithm_impl.cpp` with an allocation
failure hook immediately before feature computation, inside the original
`std::exception` catch boundary. The regression verifies that upstream wraps a
real `std::bad_alloc` as `UnknownError` zero and the binding reports unexpected
failure rather than a capture-quality outcome. Release builds use the original
algorithm source and omit the hook exports. Native error minus one means the
binding has no upstream code; zero remains the original `UnknownError`.
