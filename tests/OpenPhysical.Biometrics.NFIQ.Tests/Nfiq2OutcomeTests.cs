// SPDX-License-Identifier: GPL-2.0-or-later
using NUnit.Framework;
using OpenPhysical.Biometrics.NFIQ2;

namespace OpenPhysical.Biometrics.NFIQ.Tests;

/// <summary>Checks the managed meaning of NFIQ2 size and operational outcomes.</summary>
public sealed class Nfiq2OutcomeTests
{
    /// <summary>Separates an upstream unknown error from an unavailable error code.</summary>
    [Test]
    public void UnknownErrorIsPreservedAsAnAvailableCode()
    {
        var unknown = new Nfiq2Exception(Nfiq2NativeStatus.UnexpectedFailure, 0);
        var unavailable = new Nfiq2Exception(Nfiq2NativeStatus.AllocationFailure, -1);
        Assert.Multiple(() =>
        {
            Assert.That(unknown.HasUpstreamErrorCode, Is.True);
            Assert.That(unknown.UpstreamErrorCode, Is.Zero);
            Assert.That(unavailable.HasUpstreamErrorCode, Is.False);
        });
    }

    /// <summary>Lets applications correct image dimensions using the upstream typed outcome.</summary>
    [Test]
    public void OversizedContentPreservesInvalidImageSize()
    {
        using var engine = new Nfiq2Engine();
        var pixels = Enumerable
            .Range(0, 900 * 900)
            .Select(index => (byte)(index % 2 * 64))
            .ToArray();
        var failure = Assert.Throws<Nfiq2Exception>(() => engine.Assess(pixels, 900, 900, 500));
        Assert.Multiple(() =>
        {
            Assert.That(failure!.NativeStatus, Is.EqualTo(Nfiq2NativeStatus.AssessmentFailure));
            Assert.That(failure.UpstreamErrorCode, Is.EqualTo(14));
            Assert.That(failure.HasUpstreamErrorCode, Is.True);
        });
    }
}
