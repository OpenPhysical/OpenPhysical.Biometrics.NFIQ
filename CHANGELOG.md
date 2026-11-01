# Changelog

This project follows Semantic Versioning 2.0.0. The two algorithm packages release
together. Before 1.0, breaking changes increment the minor version.

## Unreleased

- Flatten and deduplicate Windows runtime licenses and correct extensionless
  NuGet asset paths (#14).

- Package each OpenCV library once under its loader ABI name (#13).

- Publish portable symbol packages and normalize CI build paths (#12).

- Fix CodeQL arithmetic and native correctness findings, retaining verifiable
  original NIST source receipts and adding overflow regression coverage.

## 1.0.0 - 2026-11-01

- First stable NFIQ1 and NFIQ2 package release, with the compatibility contract
  described in CONTRIBUTING.md.
- Publish both packages automatically to the OpenPhysical NuGet organization when
  a GitHub release is published, after runtime and package-consumer checks pass.
  Authentication uses NuGet trusted publishing without stored API keys.
- Run feature-branch CI on pull requests only, avoiding duplicate push checks.

- Share the runtime catalog across managed loading, native builds, release checks, CI runners, and package-consumer tests.

## 0.1.0-beta.1 - 2026-10-31

### Release review fixes

- Strengthen real-image allocation-failure coverage through the final allocation,
  checking exact failure status, cleared outputs, arena cleanup, and recovery.
- Vendor the allocation arena from its canonical NBIS source with immutable file
  receipts and a fail-closed integrity check.
- Exclude generated installation headers from the initial NIST import and verify
  the complete curated source inventory against the official archive.

- Document NFIQ2 post-trim content limits while preserving valid white-padded captures.
- Separate wrapped upstream unknown errors from assessment failures and retain whether an upstream code is available.
- Exercise native dimension, length, resolution and finger-position boundaries, plus real upstream-wrapped allocation failure.

- Select portable native assets by operating system and process architecture, including distribution-provided .NET runtimes.
- Share internal managed validation and library resolution between the independent packages, and verify real-classifier concurrency and argument boundaries.

- Add original NFIQ and NFIQ 2.3.0 buffer-based native engines and .NET 10 packages.
- Preserve original NFIQ poor-image statuses and expose typed NFIQ2 assessment failures alongside their distinct quality scales.
- Include pinned model and source provenance, five-runtime packaging, and public API documentation.
- Validate twenty SD04 impressions against independently built original NIST algorithms and published release vectors: eight NBIS NFIQ1 captures and five NFIQ2 examples.
- Explain PIV enrollment quality assessment through single-capture, paired-selection, batch LINQ, application policy, typed JSON, and input-outcome examples.
- Harden model decoding, FingerJet arithmetic, OpenCV border handling, modular vector arithmetic, and statistical dispatch while preserving reference results under halting UBSan.
- Add native µnit parity and safety checks, NUnit binding tests, coverage reports, sanitizer diagnostics, and formatting and documentation gates.
