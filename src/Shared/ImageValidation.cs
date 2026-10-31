// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.Nfiq.Internal;

internal static class ImageValidation
{
    internal static void Validate(
        ReadOnlySpan<byte> pixels,
        int width,
        int height,
        int dotsPerInch,
        int minimumDimension,
        int maximumWidth,
        int maximumHeight
    )
    {
        if (width < minimumDimension || width > maximumWidth)
            throw new ArgumentOutOfRangeException(
                nameof(width),
                $"Width must be from {minimumDimension} through {maximumWidth} pixels."
            );
        if (height < minimumDimension || height > maximumHeight)
            throw new ArgumentOutOfRangeException(
                nameof(height),
                $"Height must be from {minimumDimension} through {maximumHeight} pixels."
            );
        // Keep the multiplication wider than the public dimensions, even when an
        // algorithm's range is expanded in a later release.
        if (pixels.Length != (long)width * height)
            throw new ArgumentException(
                "The tightly packed grayscale buffer must contain width times height bytes.",
                nameof(pixels)
            );
        if (dotsPerInch != 500)
            throw new NotSupportedException(
                "Supply an explicitly identified 500 ppi fingerprint image."
            );
    }
}
