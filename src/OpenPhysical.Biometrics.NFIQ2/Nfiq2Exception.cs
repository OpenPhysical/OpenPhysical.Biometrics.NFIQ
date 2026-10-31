// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ2;

/// <summary>Identifies the native operation outcome independently of an upstream algorithm error.</summary>
public enum Nfiq2NativeStatus
{
    /// <summary>The native arguments were invalid.</summary>
    InvalidArgument = 1,

    /// <summary>Native memory allocation failed.</summary>
    AllocationFailure = 2,

    /// <summary>The image could not be assessed, including insufficient usable fingerprint area.</summary>
    AssessmentFailure = 3,

    /// <summary>The model could not be initialized.</summary>
    ModelFailure = 4,

    /// <summary>An unexpected native or dependency exception interrupted processing.</summary>
    UnexpectedFailure = 5,
}

/// <summary>Preserves a native NFIQ2 failure and its original upstream error code.</summary>
/// <remarks>Insufficient fingerprint detail can request recapture. Upstream error 14 identifies invalid usable content geometry, including blank, degenerate or oversized trimmed content. Choose recapture or dimension preparation using the capture facts. Allocation, model and unexpected failures require operational handling. Upstream UnknownError is code zero; minus one means no upstream code was supplied.</remarks>
public sealed class Nfiq2Exception : InvalidOperationException
{
    /// <summary>Creates a failure with its native category and upstream error code.</summary>
    /// <param name="nativeStatus">The native outcome category.</param>
    /// <param name="upstreamErrorCode">The numeric error from NFIQ2, including UnknownError zero, or minus one when unavailable.</param>
    public Nfiq2Exception(Nfiq2NativeStatus nativeStatus, int upstreamErrorCode)
        : base($"NFIQ2 operation failed (status {(int)nativeStatus}, code {upstreamErrorCode}).")
    {
        NativeStatus = nativeStatus;
        UpstreamErrorCode = upstreamErrorCode;
    }

    /// <summary>Gets the native failure category.</summary>
    public Nfiq2NativeStatus NativeStatus { get; }

    /// <summary>Gets the original NFIQ2 numeric error code, including UnknownError zero, or minus one when unavailable.</summary>
    public int UpstreamErrorCode { get; }

    /// <summary>Gets whether the failure carries an upstream code, including UnknownError zero.</summary>
    public bool HasUpstreamErrorCode => UpstreamErrorCode >= 0;
}
