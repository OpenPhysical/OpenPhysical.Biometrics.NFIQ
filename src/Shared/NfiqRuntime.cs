// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.Nfiq.Internal;

using System.Reflection;
using System.Runtime.InteropServices;
using System.Xml.Linq;

// Linked into each algorithm assembly so either package can be consumed independently.
internal static class NfiqRuntime
{
    internal static string CurrentRuntimeIdentifier =>
        GetRuntimeIdentifier(
            OperatingSystem.IsWindows() ? OSPlatform.Windows
                : OperatingSystem.IsLinux() ? OSPlatform.Linux
                : OperatingSystem.IsMacOS() ? OSPlatform.OSX
                : OSPlatform.Create("Unsupported"),
            RuntimeInformation.ProcessArchitecture
        );

    internal static string GetRuntimeIdentifier(OSPlatform platform, Architecture architecture)
    {
        var system =
            platform == OSPlatform.Windows ? "win"
            : platform == OSPlatform.Linux ? "linux"
            : platform == OSPlatform.OSX ? "osx"
            : "unsupported";
        var rid = system + "-" + architecture.ToString().ToLowerInvariant();
        if (Runtimes.ContainsKey(rid))
            return rid;
        throw new PlatformNotSupportedException(
            "NFIQ supports these runtimes: " + string.Join(", ", Runtimes.Keys)
        );
    }

    private static readonly IReadOnlyDictionary<
        string,
        (string Prefix, string Extension)
    > Runtimes = LoadRuntimes();

    private static IReadOnlyDictionary<string, (string Prefix, string Extension)> LoadRuntimes()
    {
        using var stream =
            typeof(NfiqRuntime).Assembly.GetManifestResourceStream(
                "OpenPhysical.Biometrics.NFIQ.runtimes.props"
            ) ?? throw new InvalidOperationException("The NFIQ runtime manifest is missing.");
        return XDocument
            .Load(stream)
            .Descendants("QualityRuntime")
            .ToDictionary(
                entry => (string)entry.Attribute("Include")!,
                entry =>
                    (
                        (string)entry.Element("NativePrefix")!,
                        (string)entry.Element("NativeExtension")!
                    ),
                StringComparer.Ordinal
            );
    }

    internal static void RegisterResolver(Assembly assembly, string libraryName)
    {
        NativeLibrary.SetDllImportResolver(
            assembly,
            (name, _, _) =>
            {
                if (name != libraryName)
                    return IntPtr.Zero;
                var runtime = CurrentRuntimeIdentifier;
                var asset = Runtimes[runtime];
                var filename = asset.Prefix + name + "." + asset.Extension;
                var candidate = Path.Combine(
                    AppContext.BaseDirectory,
                    "runtimes",
                    runtime,
                    "native",
                    filename
                );
                return NativeLibrary.TryLoad(candidate, out var library) ? library : IntPtr.Zero;
            }
        );
    }
}
