// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ1;

using System.Runtime.InteropServices;
using System.Security.Cryptography;
using Microsoft.Extensions.Logging;
using OpenPhysical.Biometrics.Nfiq.Internal;

/// <summary>Assesses fingerprint image quality with the original NIST NBIS 5.0.0 algorithm.</summary>
/// <remarks>Native calls are serialized across instances. Input pixels are copied and cleared after use.</remarks>
public sealed class Nfiq1Engine : INfiq1Engine
{
    static Nfiq1Engine() =>
        NfiqRuntime.RegisterResolver(typeof(Nfiq1Engine).Assembly, "openphysical_nfiq1");

    /// <summary>Creates an original NFIQ image-quality engine.</summary>
    /// <param name="logger">Optional operational logger. Assessment data is kept out of diagnostics.</param>
    /// <exception cref="NotSupportedException">The native ABI is unsupported.</exception>
    public Nfiq1Engine(ILogger<Nfiq1Engine>? logger = null)
    {
        _ = NfiqRuntime.CurrentRuntimeIdentifier;
        if (Native.Abi() != 1)
            throw new NotSupportedException("Unsupported NFIQ1 native ABI.");
        logger?.LogDebug(
            new EventId(1, "EngineInitialized"),
            "Fingerprint quality engine initialized."
        );
    }

    /// <summary>Assesses an optical or scanned-ink plain fingerprint image.</summary>
    /// <param name="pixels">Tightly packed, top-left-origin grayscale pixels, black zero and white 255. The buffer is borrowed for the call.</param>
    /// <param name="width">Image width from 64 through 2048 pixels.</param>
    /// <param name="height">Image height from 64 through 2048 pixels.</param>
    /// <param name="dotsPerInch">Explicit resolution, 500 pixels per inch.</param>
    /// <returns>A quality class, activation and status. Empty or low-feature images retain quality class five.</returns>
    /// <exception cref="ArgumentException">Buffer length does not match the dimensions.</exception>
    /// <exception cref="ArgumentOutOfRangeException">A dimension is outside its supported range.</exception>
    /// <exception cref="NotSupportedException">Resolution is not 500 ppi.</exception>
    /// <exception cref="InvalidOperationException">The native algorithm failed.</exception>
    public Nfiq1Assessment Assess(ReadOnlySpan<byte> pixels, int width, int height, int dotsPerInch)
    {
        ImageValidation.Validate(pixels, width, height, dotsPerInch, 64, 2048, 2048);
        var copy = pixels.ToArray();
        try
        {
            int result = Native.Assess(
                copy,
                copy.Length,
                width,
                height,
                dotsPerInch,
                out int quality,
                out float confidence,
                out int status,
                out int error
            );
            if (result != 0)
                throw new InvalidOperationException(
                    $"NFIQ1 native assessment failed (status {result}, code {error})."
                );
            return new Nfiq1Assessment(quality, confidence, (Nfiq1AssessmentStatus)status);
        }
        finally
        {
            CryptographicOperations.ZeroMemory(copy);
        }
    }

    private static class Native
    {
        [DllImport(
            "openphysical_nfiq1",
            EntryPoint = "op_nfiq1_abi_version",
            CallingConvention = CallingConvention.Cdecl
        )]
        internal static extern int Abi();

        [DllImport(
            "openphysical_nfiq1",
            EntryPoint = "op_nfiq1_assess",
            CallingConvention = CallingConvention.Cdecl
        )]
        internal static extern int Assess(
            byte[] pixels,
            int length,
            int width,
            int height,
            int dpi,
            out int quality,
            out float confidence,
            out int assessment,
            out int error
        );
    }
}
