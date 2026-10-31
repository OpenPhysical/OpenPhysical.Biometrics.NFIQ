// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ1;

/// <summary>Computes original NFIQ fingerprint image quality classes.</summary>
public interface INfiq1Engine
{
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
    Nfiq1Assessment Assess(ReadOnlySpan<byte> pixels, int width, int height, int dotsPerInch);
}
