// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ.Tests;

using NUnit.Framework;
using OpenPhysical.Biometrics.NFIQ1;
using OpenPhysical.Biometrics.NFIQ2;

[TestFixture]
internal sealed class AssessmentTests
{
    [Test]
    public void Nfiq1PreservesInputAndPoorImageOutcome()
    {
        var pixels = File.ReadAllBytes(
            Path.Combine(
                TestContext.CurrentContext.TestDirectory,
                "fixtures",
                "negative",
                "featureless.gray8"
            )
        );
        var before = pixels.ToArray();
        var engine = new Nfiq1Engine();
        var result = engine.Assess(pixels, 128, 128, 500);
        Assert.Multiple(() =>
        {
            Assert.That(result.QualityClass, Is.EqualTo(5));
            Assert.That(result.Status, Is.EqualTo(Nfiq1AssessmentStatus.TooFewMinutiae));
            Assert.That(pixels, Is.EqualTo(before));
        });
    }

    [Test]
    public void Nfiq1RejectsUnspecifiedResolution()
    {
        var engine = new Nfiq1Engine();
        Assert.Throws<NotSupportedException>(() => engine.Assess(new byte[128 * 128], 128, 128, 0));
    }

    [Test]
    public void TruncatedFixtureIsAnInputErrorRatherThanAQualityAssessment()
    {
        var pixels = File.ReadAllBytes(
            Path.Combine(
                TestContext.CurrentContext.TestDirectory,
                "fixtures",
                "negative",
                "truncated.gray8"
            )
        );
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        Assert.Multiple(() =>
        {
            Assert.Throws<ArgumentException>(() => original.Assess(pixels, 128, 128, 500));
            Assert.Throws<ArgumentException>(() => unified.Assess(pixels, 128, 128, 500));
        });
    }

    [Test]
    public void Nfiq2RejectsUseAfterDisposal()
    {
        var engine = new Nfiq2Engine();
        engine.Dispose();
        engine.Dispose();
        Assert.Throws<ObjectDisposedException>(() =>
            engine.Assess(new byte[128 * 128], 128, 128, 500)
        );
    }

    [Test]
    public void Nfiq2RejectsInconsistentImageDimensions()
    {
        using var engine = new Nfiq2Engine();
        Assert.Throws<ArgumentException>(() => engine.Assess(new byte[2], 128, 128, 500));
    }

    [Test]
    public void RealCaptureCanBeAssessedAndReusedByBothEngines()
    {
        var pixels = File.ReadAllBytes(
            Path.Combine(TestContext.CurrentContext.TestDirectory, "fixtures", "f0005_03.gray8")
        );
        var before = pixels.ToArray();
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        var first = original.Assess(pixels, 512, 512, 500);
        var second = unified.Assess(pixels, 512, 512, 500);
        Assert.Multiple(() =>
        {
            // This representative independent vector catches binding field or scale
            // mistakes; exhaustive algorithm parity stays in the native suite.
            Assert.That(first.QualityClass, Is.EqualTo(1));
            Assert.That(first.Confidence, Is.EqualTo(0.787585378f).Within(0.000001f));
            Assert.That(second.UnifiedQualityScore, Is.EqualTo(67));
            Assert.That(original.Assess(pixels, 512, 512, 500), Is.EqualTo(first));
            Assert.That(unified.Assess(pixels, 512, 512, 500), Is.EqualTo(second));
            Assert.That(pixels, Is.EqualTo(before));
        });
    }

    [Test]
    public void PublishedReleaseVectorsReachTheManagedBindingWithTheirOriginalScales()
    {
        // One representative vector per algorithm verifies the binding contract.
        // The native suite checks all published release and SD04 values.
        var directory = Path.Combine(TestContext.CurrentContext.TestDirectory, "fixtures");
        var original = new Nfiq1Engine().Assess(
            File.ReadAllBytes(Path.Combine(directory, "a011r_04.gray8")),
            552,
            600,
            500
        );
        using var engine = new Nfiq2Engine();
        var unified = engine.Assess(
            File.ReadAllBytes(Path.Combine(directory, "SFinGe_Test01.gray8")),
            416,
            560,
            500
        );
        Assert.Multiple(() =>
        {
            Assert.That(original.QualityClass, Is.EqualTo(2));
            Assert.That(original.Confidence, Is.EqualTo(0.460698754f).Within(0.000001f));
            Assert.That(unified.UnifiedQualityScore, Is.EqualTo(54));
        });
    }

    [Test]
    public void FeatureExtractionFailurePreservesTypedUpstreamOutcome()
    {
        var pixels = File.ReadAllBytes(
            Path.Combine(TestContext.CurrentContext.TestDirectory, "fixtures", "f0070_10.gray8")
        );
        using var engine = new Nfiq2Engine();
        var failure = Assert.Throws<Nfiq2Exception>(() => engine.Assess(pixels, 512, 512, 500));
        Assert.Multiple(() =>
        {
            Assert.That(failure!.NativeStatus, Is.EqualTo(Nfiq2NativeStatus.AssessmentFailure));
            Assert.That(failure.UpstreamErrorCode, Is.EqualTo(11));
        });
    }

    [Test]
    public void Nfiq1ConcurrentAssessmentsAreConsistent()
    {
        var engine = new Nfiq1Engine();
        var pixels = File.ReadAllBytes(
            Path.Combine(TestContext.CurrentContext.TestDirectory, "fixtures", "f0005_03.gray8")
        );
        var before = pixels.ToArray();
        var results = Enumerable
            .Range(0, 8)
            .AsParallel()
            .Select(index =>
                (index % 2 == 0 ? engine : new Nfiq1Engine()).Assess(pixels, 512, 512, 500)
            )
            .ToArray();
        Assert.Multiple(() =>
        {
            Assert.That(results.Select(result => result.QualityClass), Is.All.EqualTo(1));
            Assert.That(
                results.Select(result => result.Status),
                Is.All.EqualTo(Nfiq1AssessmentStatus.Assessed)
            );
            Assert.That(
                results.Select(result => result.Confidence),
                Is.All.EqualTo(0.787585378f).Within(0.000001f)
            );
            Assert.That(pixels, Is.EqualTo(before));
        });
    }
}
