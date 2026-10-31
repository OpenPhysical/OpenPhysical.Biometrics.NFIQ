// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ1;

/// <summary>Describes how the original NFIQ assessment obtained its quality class.</summary>
public enum Nfiq1AssessmentStatus
{
    /// <summary>The classifier assessed the image normally.</summary>
    Assessed = 0,

    /// <summary>The image was empty and received quality class five.</summary>
    EmptyImage = 1,

    /// <summary>Too few minutiae were detected and the image received quality class five.</summary>
    TooFewMinutiae = 2,
}

/// <summary>Contains an original NFIQ quality class and classifier output.</summary>
/// <param name="QualityClass">Quality class from one (best) through five (worst).</param>
/// <param name="Confidence">Maximum classifier activation, distinct from a calibrated probability.</param>
/// <param name="Status">Normal classification or a defined poor-image outcome.</param>
public sealed record Nfiq1Assessment(
    int QualityClass,
    float Confidence,
    Nfiq1AssessmentStatus Status
);
