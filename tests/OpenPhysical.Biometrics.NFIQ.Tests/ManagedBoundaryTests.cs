// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ.Tests;

using System.Runtime.InteropServices;
using System.Xml.Linq;
using NUnit.Framework;
using OpenPhysical.Biometrics.Nfiq.Internal;
using OpenPhysical.Biometrics.NFIQ1;
using OpenPhysical.Biometrics.NFIQ2;

[TestFixture]
internal sealed class ManagedBoundaryTests
{
    private static IEnumerable<TestCaseData> RuntimeMappings()
    {
        var manifest = XDocument.Load(
            Path.Combine(TestContext.CurrentContext.TestDirectory, "runtimes.props")
        );
        foreach (var entry in manifest.Descendants("QualityRuntime"))
        {
            var rid = (string)entry.Attribute("Include")!;
            var parts = rid.Split('-');
            var platform = parts[0] switch
            {
                "win" => OSPlatform.Windows,
                "linux" => OSPlatform.Linux,
                "osx" => OSPlatform.OSX,
                _ => throw new InvalidOperationException(
                    "Runtime catalog contains an unknown operating system."
                ),
            };
            yield return new TestCaseData(platform, Enum.Parse<Architecture>(parts[1], true), rid);
        }
    }

    [TestCaseSource(nameof(RuntimeMappings))]
    public void PortableAssetsAreSelectedFromTheOperatingSystemAndProcess(
        OSPlatform platform,
        Architecture architecture,
        string expected
    ) =>
        Assert.That(NfiqRuntime.GetRuntimeIdentifier(platform, architecture), Is.EqualTo(expected));

    [Test]
    public void UnsupportedProcessesAreRejectedBeforeNativeLoading()
    {
        Assert.Throws<PlatformNotSupportedException>(() =>
            NfiqRuntime.GetRuntimeIdentifier(OSPlatform.Windows, Architecture.Arm64)
        );
        Assert.Throws<PlatformNotSupportedException>(() =>
            NfiqRuntime.GetRuntimeIdentifier(OSPlatform.Linux, Architecture.X86)
        );
        Assert.Throws<PlatformNotSupportedException>(() =>
            NfiqRuntime.GetRuntimeIdentifier(OSPlatform.Create("FreeBSD"), Architecture.X64)
        );
    }

    [TestCase(-1, 128, "width")]
    [TestCase(0, 128, "width")]
    [TestCase(63, 128, "width")]
    [TestCase(2049, 128, "width")]
    [TestCase(128, -1, "height")]
    [TestCase(128, 0, "height")]
    [TestCase(128, 63, "height")]
    [TestCase(128, 2049, "height")]
    [TestCase(int.MaxValue, int.MaxValue, "width")]
    [TestCase(65536, 65536, "width")]
    public void DimensionsAreValidatedBeforeMultiplicationOrNativeCalls(
        int width,
        int height,
        string parameter
    )
    {
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        Assert.Multiple(() =>
        {
            Assert.That(
                Assert
                    .Throws<ArgumentOutOfRangeException>(() =>
                        original.Assess([], width, height, 500)
                    )!
                    .ParamName,
                Is.EqualTo(parameter)
            );
            Assert.That(
                Assert
                    .Throws<ArgumentOutOfRangeException>(() =>
                        unified.Assess([], width, height, 500)
                    )!
                    .ParamName,
                Is.EqualTo(parameter)
            );
        });
    }

    [TestCase(64, 64)]
    [TestCase(64, 2048)]
    [TestCase(2048, 64)]
    [TestCase(2048, 2048)]
    public void DimensionEndpointsProceedToPixelCountValidation(int width, int height)
    {
        // Empty pixels isolate the wrapper's dimension contract from the algorithm's
        // later assessment of fingerprint content and trimmed image dimensions.
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        Assert.Multiple(() =>
        {
            Assert.That(
                Assert
                    .Throws<ArgumentException>(() => original.Assess([], width, height, 500))!
                    .ParamName,
                Is.EqualTo("pixels")
            );
            Assert.That(
                Assert
                    .Throws<ArgumentException>(() => unified.Assess([], width, height, 500))!
                    .ParamName,
                Is.EqualTo("pixels")
            );
        });
    }

    [Test]
    public void SharedPixelCountValidationKeepsMultiplicationWiderThanTheDimensions()
    {
        var exception = Assert.Throws<ArgumentException>(() =>
            ImageValidation.Validate([], 65536, 65536, 500, 1, int.MaxValue, int.MaxValue)
        );
        Assert.That(exception!.ParamName, Is.EqualTo("pixels"));
    }

    [TestCase(4095)]
    [TestCase(4097)]
    public void BothEnginesRequireTheExactPixelCount(int length)
    {
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        Assert.Multiple(() =>
        {
            Assert.That(
                Assert
                    .Throws<ArgumentException>(() =>
                        original.Assess(new byte[length], 64, 64, 500)
                    )!
                    .ParamName,
                Is.EqualTo("pixels")
            );
            Assert.That(
                Assert
                    .Throws<ArgumentException>(() => unified.Assess(new byte[length], 64, 64, 500))!
                    .ParamName,
                Is.EqualTo("pixels")
            );
        });
    }

    [TestCase(-1)]
    [TestCase(0)]
    [TestCase(499)]
    [TestCase(501)]
    [TestCase(1000)]
    public void BothEnginesRequireExplicitFiveHundredPpi(int resolution)
    {
        var original = new Nfiq1Engine();
        using var unified = new Nfiq2Engine();
        var pixels = new byte[64 * 64];
        Assert.Throws<NotSupportedException>(() => original.Assess(pixels, 64, 64, resolution));
        Assert.Throws<NotSupportedException>(() => unified.Assess(pixels, 64, 64, resolution));
    }

    [TestCase((byte)11)]
    [TestCase(byte.MaxValue)]
    public void Nfiq2RejectsFingerPositionsOutsideTheIsoRange(byte finger)
    {
        using var engine = new Nfiq2Engine();
        var exception = Assert.Throws<ArgumentOutOfRangeException>(() =>
            engine.Assess(new byte[64 * 64], 64, 64, 500, finger)
        );
        Assert.That(exception!.ParamName, Is.EqualTo("fingerPosition"));
    }

    [TestCase((byte)0)]
    [TestCase((byte)10)]
    public void Nfiq2AcceptsBothFingerPositionEndpoints(byte finger)
    {
        using var engine = new Nfiq2Engine();
        var pixels = File.ReadAllBytes(
            Path.Combine(TestContext.CurrentContext.TestDirectory, "fixtures", "f0005_03.gray8")
        );
        Assert.That(
            engine.Assess(pixels, 512, 512, 500, finger).UnifiedQualityScore,
            Is.EqualTo(67)
        );
    }
}
