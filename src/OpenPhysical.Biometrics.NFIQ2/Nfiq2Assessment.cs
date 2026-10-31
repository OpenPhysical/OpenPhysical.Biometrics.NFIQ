// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ2;

/// <summary>Contains the unified quality score from NFIQ 2.3.0 and its pinned optical/ink model.</summary>
/// <param name="UnifiedQualityScore">Quality from zero through 100, where higher values indicate better predicted recognition performance.</param>
public sealed record Nfiq2Assessment(int UnifiedQualityScore);
