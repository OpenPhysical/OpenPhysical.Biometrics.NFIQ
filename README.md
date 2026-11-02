# OpenPhysical.Biometrics.NFIQ

**Assess fingerprint image quality from .NET 10**, using NIST's original NFIQ algorithm and NFIQ 2.3.0.

A fingerprint reader can produce several impressions of the same finger. This
library helps an enrollment application assess those captures, choose an image
to retain, and explain when another impression would help. Each assessment keeps
the algorithm's original quality scale and outcome.

The shared package version is **1.0.0**, the first stable release. Packages are
published under the **OpenPhysical** NuGet organization. The links below show
the current publication status; a release becomes installable only after the
[publishing workflow](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/actions/workflows/publish.yml)
and NuGet validation finish.

[![NFIQ1 on NuGet](https://img.shields.io/nuget/v/OpenPhysical.Biometrics.NFIQ1)](https://www.nuget.org/packages/OpenPhysical.Biometrics.NFIQ1)
[![NFIQ2 on NuGet](https://img.shields.io/nuget/v/OpenPhysical.Biometrics.NFIQ2)](https://www.nuget.org/packages/OpenPhysical.Biometrics.NFIQ2)

Choose the package that fits your workflow:

- `OpenPhysical.Biometrics.NFIQ1` returns a **class from 1 to 5**, with 1 best,
  together with the original classifier confidence and capture status.
- `OpenPhysical.Biometrics.NFIQ2` returns a **score from 0 to 100**, with higher
  values indicating better predicted recognition performance. Each engine loads
  and reuses the NFIQ 2.3.0 optical/ink random-forest model.

## Built from NIST's reference code

We started with NIST's original NBIS 5.0.0 NFIQ source and the NFIQ 2.3.0 release,
then adapted them for .NET applications. The algorithms still run in native C and
C++. A C# API accepts grayscale pixels directly and returns typed results in the
same process.

Our additions handle input validation, memory cleanup, concurrent calls, native
library loading, and .NET integration. The original NIST files are preserved
unmodified in the first Git commit. Build-time adaptations stay separate, so their
purpose and effect can be reviewed against that starting point.

The [provenance record](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/native/PROVENANCE.md) identifies the source checksums,
dependency versions and adaptations. The [changelog](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/CHANGELOG.md) records changes
to the .NET library.

## Where it fits in PIV

Personal Identity Verification (PIV) enrollment starts with fingerprint captures.
An enrollment application assesses each impression, selects the captures to use,
and carries their quality information into the biometric record.

The PIV minutiae profile uses original NFIQ classes. Its image-quality value is
`20 * (6 - qualityClass)`, so NFIQ class 1 becomes 100 and class 5 becomes 20.
NFIQ2 provides its own quality measurement for acquisition and capture-selection
workflows. Keep both measurements with their algorithm versions when storing
assessment results.

## Using the libraries

Install either or both packages once version 1.0.0 is available on NuGet:

```sh
dotnet add package OpenPhysical.Biometrics.NFIQ1 --version 1.0.0
dotnet add package OpenPhysical.Biometrics.NFIQ2 --version 1.0.0
```

Both packages accept tightly packed, top-left-origin, 8-bit grayscale pixels.
Black is 0 and white is 255. Supply dimensions and **500 ppi** explicitly; each
dimension must be from 64 through 2048 pixels for bounded buffer handling.
NFIQ2 trims white margins before assessing the fingerprint content. That trimmed
content must fit within **800 pixels wide and 1000 pixels high**. Upstream
`InvalidImageSize` code **14** describes invalid usable content geometry,
including blank or degenerate trimmed content and content exceeding those limits.
Use the capture facts to choose recapture for missing fingerprint content or
correctly sized preparation for oversized content.
White padding around a supported fingerprint remains valid. Small captures may
have too little fingerprint area to assess. Decode reader output to grayscale
pixels before calling the engines.

```csharp
using OpenPhysical.Biometrics.NFIQ1;
using OpenPhysical.Biometrics.NFIQ2;

var original = new Nfiq1Engine();
Nfiq1Assessment first = original.Assess(pixels, width, height, dotsPerInch: 500);

using var unified = new Nfiq2Engine();
Nfiq2Assessment second = unified.Assess(pixels, width, height, dotsPerInch: 500);
```

Reuse the engines across captures. Materialize a LINQ sequence when the results
will be filtered or reviewed more than once:

```csharp
var assessments = captures
    .Select(capture => original.Assess(capture.Pixels, capture.Width, capture.Height, 500))
    .ToArray();
```

`Nfiq1Assessment.Status` distinguishes a normal assessment from the original
algorithm's empty-image and too-few-minutiae outcomes. Those defined outcomes
retain quality class 5 and confidence 1. When NFIQ2 cannot assess a capture,
`Nfiq2Exception.NativeStatus` and `UpstreamErrorCode` preserve the outcome. An
application can request recapture for insufficient fingerprint detail, handle
code 14 according to the usable content geometry, and handle memory, model or
unexpected native failures as operational problems. Upstream `UnknownError`
code **0** is an unexpected failure, including exceptions that NFIQ2 wraps before
they reach the binding. `HasUpstreamErrorCode` distinguishes that real code from
**-1**, the binding's unavailable-code sentinel.

The [runnable workflows](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/examples/OpenPhysical.Biometrics.NFIQ.Examples/QualityWorkflows.cs)
show a single capture, paired SD04 impressions, LINQ-based candidate selection,
typed JSON records, and poor-capture/malformed-input handling. Comments explain
how each step fits an enrollment application. Example selection limits are
supplied by application policy. Console output reports workflow status while
assessment values stay in memory.

```sh
dotnet run --project examples/OpenPhysical.Biometrics.NFIQ.Examples -c Release -- capture.gray8 512 512
dotnet run --project examples/OpenPhysical.Biometrics.NFIQ.Examples -c Release -- --sd04 tests/fixtures
```

For dependency injection, call `services.AddNfiq1()` or `services.AddNfiq2()` from
the corresponding namespace. NFIQ2 engines are disposable; the service provider
manages their lifetime. Calls serialize within each NFIQ2 context and across the
NFIQ1 native library. Logging uses `Microsoft.Extensions.Logging` and reports
operational status. Public APIs include XML documentation for IntelliSense.

## Build and test

Install .NET 10, Python 3, CMake 3.20+ and a C/C++ compiler with C++20 support for FingerJet. Windows uses the MSYS2
UCRT64 GCC toolchain. Clone with `git clone --recurse-submodules` to retrieve the
pinned NFIQ2 dependencies.

```sh
python scripts/build-native.py --algorithm nfiq1
python scripts/build-native.py --algorithm nfiq2
python scripts/build-native.py --algorithm nfiq1 --tests
python scripts/build-native.py --algorithm nfiq2 --tests
dotnet tool restore
dotnet csharpier check src tests/OpenPhysical.Biometrics.NFIQ.Tests examples
dotnet test OpenPhysical.Biometrics.NFIQ.slnx -c Release
```

Pass `--sanitizer asan` or `--sanitizer ubsan` for separate instrumented native test
builds. Package native assets are unsanitized release builds. The runtime
identifiers and CI runners are defined in [runtimes.props](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/runtimes.props).
Asset selection uses the operating system and process architecture, including
.NET installations supplied by Linux distributions. Linux builds
use Ubuntu 22.04 (glibc 2.35). Native macOS deployment target is 12; .NET 10's host
support requires macOS 14 or later. Run managed builds and tests serially.

Complete release packing requires every algorithm runtime directory listed in `runtimes.props`. Local
package checks can use `-p:AllowPartialQualityRuntimes=true`. Each package contains
only its own native algorithm and runtime dependencies. NFIQ2's replaceable
FingerJet and OpenCV shared libraries travel alongside the wrapper.

## Testing and contributing

Publishing a GitHub release automatically validates and publishes both packages
through NuGet trusted publishing, without stored API keys. See the
[release guide](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/docs/RELEASING.md) and [changelog](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/CHANGELOG.md). Feature branches
run checks on pull requests only; `master` also runs checks after pushes.

The [validation record](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/docs/VALIDATION.md) explains how we compare the adapted
library with NIST's reference code. Our fixtures include twenty SD04 impressions,
eight published NBIS NFIQ1 release captures and five published NFIQ2 examples.
µnit owns exact native algorithm results and memory-safety checks; NUnit checks
the .NET binding, typed outcomes and reuse workflows. CI retains native and managed
coverage reports. CSharpier formatting and complete public XML documentation are
required build gates.

See [contributing](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/CONTRIBUTING.md) for development and contributor terms,
the [Bounded Contribution Policy](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/CODE_OF_CONDUCT.md) for participation, and
[security reporting](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/SECURITY.md) for privately reporting a vulnerability.

## Source and licensing

[Source provenance](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/native/PROVENANCE.md) records the official upstream releases,
source checksums, dependency pins and adaptations. The first commit imports the
original source. First-party code is GPL-2.0-or-later with commercial licensing
available under [the project terms](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/COMMERCIAL-LICENSING.md). NFIQ2 dependencies
retain their LGPLv3, Apache 2.0 and public-domain terms; see
[third-party notices](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/THIRD_PARTY_NOTICES.md) and the corresponding-source and
replacement instructions there. Fixtures credit Craig I. Watson and NIST.

### Bundled native licenses

NFIQ2 includes OpenCV (Apache-2.0), FingerJetFX OSE (LGPL-3.0-or-later),
and digestpp (Unlicense), alongside NIST's own notices and the first-party
GPL-2.0-or-later binding. Its NuGet license metadata points to the
[component license inventory](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/NFIQ2-PACKAGE-LICENSE.md).
Full license texts ship in `licenses/`; Windows runtime notices also ship under
`runtimes/win-x64/native/licenses/`. See
[third-party notices](https://github.com/OpenPhysical/OpenPhysical.Biometrics.NFIQ/blob/master/THIRD_PARTY_NOTICES.md)
for corresponding-source and replacement instructions.
