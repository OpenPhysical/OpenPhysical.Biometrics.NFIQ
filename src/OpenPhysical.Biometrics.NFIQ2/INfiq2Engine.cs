// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ2;

/// <summary>Computes unified fingerprint image quality with NFIQ 2.</summary>
public interface INfiq2Engine : IDisposable
{
    /// <summary>Assesses an optical or scanned-ink plain fingerprint image.</summary>
    /// <param name="pixels">Tightly packed, top-left-origin grayscale pixels, black zero and white 255. The buffer is borrowed for the call.</param>
    /// <param name="width">Buffer width from 64 through 2048 pixels. After upstream white-margin trimming, fingerprint content must be at most 800 pixels wide.</param>
    /// <param name="height">Buffer height from 64 through 2048 pixels. After upstream white-margin trimming, fingerprint content must be at most 1000 pixels high.</param>
    /// <param name="dotsPerInch">Explicit resolution, 500 pixels per inch.</param>
    /// <param name="fingerPosition">ISO finger position zero (unspecified) or one through ten.</param>
    /// <returns>The unified quality score from zero through 100.</returns>
    /// <exception cref="ArgumentException">Buffer length does not match the dimensions.</exception>
    /// <exception cref="ArgumentOutOfRangeException">A dimension or finger position is outside its supported range.</exception>
    /// <exception cref="NotSupportedException">Resolution is not 500 ppi.</exception>
    /// <exception cref="ObjectDisposedException">The engine has been disposed.</exception>
    /// <exception cref="Nfiq2Exception">The image could not be assessed, or a native operation failed. Inspect its typed status and upstream code.</exception>
    /// <remarks>The dimensions bound input allocation. NFIQ2 trims white margins, then rejects content exceeding 800 by 1000 pixels with an assessment failure and upstream code 14. Small images may lack enough usable fingerprint area.</remarks>
    Nfiq2Assessment Assess(
        ReadOnlySpan<byte> pixels,
        int width,
        int height,
        int dotsPerInch,
        byte fingerPosition = 0
    );
}
