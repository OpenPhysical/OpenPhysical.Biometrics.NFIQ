// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 Mistial Developer

namespace OpenPhysical.Biometrics.NFIQ.Examples;

using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text.Json;
using OpenPhysical.Biometrics.NFIQ1;
using OpenPhysical.Biometrics.NFIQ2;

internal static class QualityWorkflows
{
    internal static void RunCapture(string path, int width, int height)
    {
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        var assessment = AssessFile(original, unified, path, width, height, 500);
        VerifyJsonRoundTrip([assessment]);
        DemonstrateInputOutcomes(original, unified);
    }

    internal static void RunSd04(string directory)
    {
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        using var manifest = JsonDocument.Parse(
            File.ReadAllText(Path.Combine(directory, "provenance.json"))
        );
        var images = manifest
            .RootElement.GetProperty("images")
            .EnumerateArray()
            .Select(image => new CaptureMetadata(
                image.GetProperty("pair_id").GetString()!,
                image.GetProperty("raw").GetString()!,
                image.GetProperty("width").GetInt32(),
                image.GetProperty("height").GetInt32(),
                image.GetProperty("dots_per_inch").GetInt32()
            ))
            .ToArray();

        // The manifest keeps the two impressions of each finger together and
        // supplies acquisition metadata. Finish each pair before loading another.
        var selected = new List<CaptureAssessment>();
        foreach (var pair in images.GroupBy(image => image.PairId))
        {
            // Select describes the assessments; ToImmutableArray runs them once.
            // Later filtering and ordering reuse the recorded results.
            var assessments = pair.Select(image =>
                    AssessFile(
                        original,
                        unified,
                        Path.Combine(directory, image.Filename),
                        image.Width,
                        image.Height,
                        image.DotsPerInch
                    )
                )
                .ToImmutableArray();
            var candidates = SelectCandidates(
                assessments,
                maximumOriginalClass: 3,
                minimumUnifiedScore: 40
            );
            if (!candidates.IsEmpty)
                selected.Add(candidates[0]);
        }
        VerifyJsonRoundTrip(selected.ToImmutableArray());
        DemonstrateInputOutcomes(original, unified, directory);
    }

    private static CaptureAssessment AssessFile(
        Nfiq1Engine original,
        Nfiq2Engine unified,
        string path,
        int width,
        int height,
        int dotsPerInch
    )
    {
        var pixels = File.ReadAllBytes(path);
        try
        {
            // Keep both measurements with their own scale and algorithm version.
            // NFIQ1 class 1 is best; NFIQ2 scores increase toward 100.
            var first = original.Assess(pixels, width, height, dotsPerInch);
            try
            {
                var second = unified.Assess(pixels, width, height, dotsPerInch);
                return new(first, second, null, null, "NBIS 5.0.0 NFIQ", "NFIQ 2.3.0 optical/ink");
            }
            catch (Nfiq2Exception failure)
                when (failure.NativeStatus == Nfiq2NativeStatus.AssessmentFailure)
            {
                // A capture with too little usable fingerprint area can need
                // recapture. Code 14 means invalid usable content geometry: blank,
                // degenerate, or larger than 800 by 1000 pixels after trimming.
                // Use the capture facts to choose recapture or size preparation.
                // Preserve the typed outcome and original error code.
                // Allocation, model and unexpected failures propagate to the caller.
                return new(
                    first,
                    null,
                    failure.NativeStatus,
                    failure.UpstreamErrorCode,
                    "NBIS 5.0.0 NFIQ",
                    "NFIQ 2.3.0 optical/ink"
                );
            }
        }
        finally
        {
            // Both calls finish synchronously. Clear the temporary reading buffer
            // after the assessments have copied the values they need.
            CryptographicOperations.ZeroMemory(pixels);
        }
    }

    private static ImmutableArray<CaptureAssessment> SelectCandidates(
        ImmutableArray<CaptureAssessment> assessments,
        int maximumOriginalClass,
        int minimumUnifiedScore
    )
    {
        // These illustrative limits belong to application policy. An enrollment
        // system supplies limits evaluated for its readers and acquisition process.
        // Classifier confidence belongs to NFIQ1 and stays with its typed result.
        return assessments
            .Where(result =>
                result.Original.Status == Nfiq1AssessmentStatus.Assessed
                && result.Original.QualityClass <= maximumOriginalClass
                && result.Unified is not null
                && result.Unified.UnifiedQualityScore >= minimumUnifiedScore
            )
            .OrderByDescending(result => result.Unified!.UnifiedQualityScore)
            .ToImmutableArray();
    }

    private static void VerifyJsonRoundTrip(ImmutableArray<CaptureAssessment> assessments)
    {
        // A protected enrollment record can retain results and their provenance.
        // Keep this demonstration in memory, including its quality measurements.
        var json = JsonSerializer.Serialize(assessments);
        var restored = JsonSerializer.Deserialize<ImmutableArray<CaptureAssessment>>(json);
        if (!assessments.SequenceEqual(restored))
            throw new InvalidOperationException("Assessment JSON round trip differed.");
    }

    private static void DemonstrateInputOutcomes(
        Nfiq1Engine original,
        Nfiq2Engine unified,
        string? fixtureDirectory = null
    )
    {
        // A featureless white image has no usable ridge detail. The original
        // algorithm preserves its defined class 5 / TooFewMinutiae outcome.
        var featureless = fixtureDirectory is null
            ? Enumerable.Repeat((byte)255, 128 * 128).ToArray()
            : File.ReadAllBytes(Path.Combine(fixtureDirectory, "negative", "featureless.gray8"));
        byte[] truncated = [];
        try
        {
            truncated = fixtureDirectory is null
                ? new byte[] { 0, 255 }
                : File.ReadAllBytes(Path.Combine(fixtureDirectory, "negative", "truncated.gray8"));
            var poorCapture = original.Assess(featureless, 128, 128, 500);
            if (
                poorCapture.Status != Nfiq1AssessmentStatus.TooFewMinutiae
                || poorCapture.QualityClass != 5
            )
                throw new InvalidOperationException("The featureless capture outcome differed.");
            try
            {
                _ = unified.Assess(featureless, 128, 128, 500);
                throw new InvalidOperationException(
                    "The featureless capture unexpectedly received a score."
                );
            }
            catch (Nfiq2Exception failure)
                when (failure.NativeStatus == Nfiq2NativeStatus.AssessmentFailure)
            {
                // An enrollment application can preserve this outcome and ask
                // the operator to capture another impression.
                _ = failure.UpstreamErrorCode;
            }
            try
            {
                // A truncated buffer is an input error, separate from poor quality.
                _ = original.Assess(truncated, 128, 128, 500);
                throw new InvalidOperationException("The malformed buffer was accepted.");
            }
            catch (ArgumentException)
            {
                // Correct the acquisition metadata or buffer before retrying.
            }
        }
        finally
        {
            CryptographicOperations.ZeroMemory(featureless);
            CryptographicOperations.ZeroMemory(truncated);
        }
    }

    private sealed record CaptureMetadata(
        string PairId,
        string Filename,
        int Width,
        int Height,
        int DotsPerInch
    );

    private sealed record CaptureAssessment(
        Nfiq1Assessment Original,
        Nfiq2Assessment? Unified,
        Nfiq2NativeStatus? FailureStatus,
        int? UpstreamErrorCode,
        string OriginalAlgorithm,
        string UnifiedAlgorithm
    );
}
