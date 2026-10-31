// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 Mistial Developer

using System.Globalization;
using OpenPhysical.Biometrics.NFIQ.Examples;

if (args is not ["--sd04", _] && args.Length != 3)
{
    Console.WriteLine("Examples <capture.gray8> <width> <height>");
    Console.WriteLine("Examples --sd04 <fixture-directory>");
    return 2;
}

try
{
    if (args is ["--sd04", var directory])
        QualityWorkflows.RunSd04(directory);
    else
        QualityWorkflows.RunCapture(
            args[0],
            int.Parse(args[1], CultureInfo.InvariantCulture),
            int.Parse(args[2], CultureInfo.InvariantCulture)
        );
    Console.WriteLine("Fingerprint quality workflows completed successfully.");
    return 0;
}
catch (Exception error)
    when (error
            is ArgumentException
                or FormatException
                or IOException
                or UnauthorizedAccessException
                or NotSupportedException
                or InvalidOperationException
                or DllNotFoundException
                or BadImageFormatException
                or EntryPointNotFoundException
                or OverflowException
                or System.Text.Json.JsonException
    )
{
    // Keep operational feedback useful without printing capture paths or results.
    Console.Error.WriteLine(
        "Example failed. Check capture metadata, fixture files, and native runtime installation."
    );
    return 1;
}
