# Security Policy

## Supported versions

Security fixes currently target the `master` branch. Older commits, development
branches, and historical upstream NFIQ releases are not separately maintained by
this project. Support commitments for versioned releases will be listed here when
adopted. Include the exact commit or package version in a report.

## Reporting a vulnerability

Email [security@mistial.dev](mailto:security@mistial.dev) with the subject:

```text
[OpenPhysical.Biometrics.NFIQ Security] Brief description
```

Please do not open a public issue, pull request, or discussion containing a suspected
vulnerability before we have had a reasonable opportunity to investigate and coordinate
a fix. This reporting route does not depend on GitHub private reporting being enabled.

Include as much of the following as is available:

- The affected commit or package version, native ABI version if known, and whether
  you used the native library, .NET API, or example application.
- Operating system, process architecture/RID, .NET runtime, compiler, and build flags.
- A concise impact assessment and the conditions needed to trigger the issue.
- Reproduction steps or a minimal test case using synthetic data or public NIST fixtures.
- Relevant redacted diagnostics, native status codes, or ASan/UBSan output.
- Suggested remediation and whether you would like public credit.

Do not send live fingerprint images, minutiae templates, personal identity data,
card dumps, PINs, credentials, or private keys. Prefer synthetic examples or identify
the relevant public fixture. If other sensitive material is needed, send a minimal
initial report and arrange an encrypted channel before sharing it. Review sanitizer
output and crash dumps for biometric buffers, memory contents, and local paths before
sending them.

No contributor assignment is required to report a vulnerability. Code patches
submitted for inclusion follow [CONTRIBUTING.md](CONTRIBUTING.md).

## What to expect

Following the existing OpenPhysical reporting policy, our response targets are:

- Acknowledgement within five business days.
- An initial assessment or status update within ten business days.
- An update at least every fourteen days while an accepted report remains open.

These are targets, not guarantees. Reproduction on another platform or coordination
with upstream maintainers may require more time. If you receive no acknowledgement,
please follow up at the same address.

We will investigate the report, assess its impact, and coordinate a remediation and
disclosure timeline with the reporter. When appropriate, we will publish an advisory,
request a CVE, and credit the reporter with their permission. This policy does not offer
a bug bounty or guarantee a CVE assignment or a particular resolution date.

## Scope

This policy covers vulnerabilities affecting this project's:

- Vendored NFIQ1/NFIQ2 algorithms and the native C ABI, including memory safety,
  allocation-failure recovery, concurrency, and input handling.
- .NET interop, image validation, quality-result handling and model lifetime.
- Example input/output handling and unintended exposure of biometric information.
- Native library loading, runtime packaging, and build/release artifact integrity.

Please report upstream NFIQ or dependency vulnerabilities when they can be exploited
through this project. We may need to mitigate them here while coordinating with the
upstream maintainer. Defects unrelated to this integration belong with the appropriate
upstream project, but uncertainty about ownership should not prevent an initial report.

Quality-assessment reports should identify a distinct security impact and reproducible conditions. Scanner output
alone is not sufficient to establish a vulnerability; include a concrete affected path
when possible. Ordinary feature requests and non-security bugs may use public issues.

## Research and deployment boundaries

Test only systems and data you own or are authorized to use. Avoid privacy violations,
unnecessary disruption, or access beyond what is needed to demonstrate the issue.
Do not test other people's deployed services without their permission.

The native engine executes inside the hosting process. Applications provide access
controls, deployment isolation, resource limits, package provenance, and protection
of stored or exported biometric data. Quality results support application-controlled
recapture and enrollment decisions.

See the [build and API guide](README.md) for input requirements and runtime
behavior, and [source provenance](native/PROVENANCE.md) for upstream adaptations.
