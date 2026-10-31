// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ2;

using System.Runtime.InteropServices;
using System.Security.Cryptography;
using Microsoft.Extensions.Logging;
using Microsoft.Win32.SafeHandles;
using OpenPhysical.Biometrics.Nfiq.Internal;

/// <summary>Assesses fingerprint quality using NFIQ 2.3.0 and its embedded optical/ink model.</summary>
/// <remarks>Reuse an instance to reuse its model. Native calls serialize per instance and disposal waits for active calls.</remarks>
public sealed class Nfiq2Engine : INfiq2Engine
{
    static Nfiq2Engine() =>
        NfiqRuntime.RegisterResolver(typeof(Nfiq2Engine).Assembly, "openphysical_nfiq2");

    private readonly ModelHandle handle;
    private readonly object gate = new();

    /// <summary>Loads the pinned model into a reusable native context.</summary>
    /// <param name="logger">Optional operational logger. Assessment data is kept out of diagnostics.</param>
    /// <exception cref="NotSupportedException">The native ABI is unsupported.</exception>
    /// <exception cref="Nfiq2Exception">The native model could not be initialized.</exception>
    public Nfiq2Engine(ILogger<Nfiq2Engine>? logger = null)
    {
        _ = NfiqRuntime.CurrentRuntimeIdentifier;
        if (Native.Abi() != 1)
            throw new NotSupportedException("Unsupported NFIQ2 native ABI.");
        var result = Native.Create(out var pointer, out int error);
        if (result != 0)
            throw new Nfiq2Exception((Nfiq2NativeStatus)result, error);
        handle = new ModelHandle(pointer);
        logger?.LogDebug(
            new EventId(2, "EngineInitialized"),
            "Fingerprint quality engine initialized."
        );
    }

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
    public Nfiq2Assessment Assess(
        ReadOnlySpan<byte> pixels,
        int width,
        int height,
        int dotsPerInch,
        byte fingerPosition = 0
    )
    {
        ImageValidation.Validate(pixels, width, height, dotsPerInch, 64, 2048, 2048);
        if (fingerPosition > 10)
            throw new ArgumentOutOfRangeException(nameof(fingerPosition));
        lock (gate)
        {
            ObjectDisposedException.ThrowIf(handle.IsClosed, this);
            var copy = pixels.ToArray();
            try
            {
                int result = Native.Assess(
                    handle,
                    copy,
                    copy.Length,
                    width,
                    height,
                    dotsPerInch,
                    fingerPosition,
                    out int score,
                    out int error
                );
                if (result != 0)
                    throw new Nfiq2Exception((Nfiq2NativeStatus)result, error);
                return new Nfiq2Assessment(score);
            }
            finally
            {
                CryptographicOperations.ZeroMemory(copy);
            }
        }
    }

    /// <summary>Releases the model after any active assessment completes.</summary>
    public void Dispose()
    {
        lock (gate)
            handle.Dispose();
    }

    private sealed class ModelHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        internal ModelHandle(IntPtr pointer)
            : base(true)
        {
            SetHandle(pointer);
        }

        protected override bool ReleaseHandle()
        {
            Native.Destroy(handle);
            return true;
        }
    }

    private static class Native
    {
        [DllImport(
            "openphysical_nfiq2",
            EntryPoint = "op_nfiq2_abi_version",
            CallingConvention = CallingConvention.Cdecl
        )]
        internal static extern int Abi();

        [DllImport(
            "openphysical_nfiq2",
            EntryPoint = "op_nfiq2_create",
            CallingConvention = CallingConvention.Cdecl
        )]
        internal static extern int Create(out IntPtr context, out int error);

        [DllImport(
            "openphysical_nfiq2",
            EntryPoint = "op_nfiq2_destroy",
            CallingConvention = CallingConvention.Cdecl
        )]
        internal static extern void Destroy(IntPtr context);

        [DllImport(
            "openphysical_nfiq2",
            EntryPoint = "op_nfiq2_assess",
            CallingConvention = CallingConvention.Cdecl
        )]
        internal static extern int Assess(
            ModelHandle context,
            byte[] pixels,
            int length,
            int width,
            int height,
            int dpi,
            int finger,
            out int score,
            out int error
        );
    }
}
