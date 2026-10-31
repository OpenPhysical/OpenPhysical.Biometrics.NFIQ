// SPDX-License-Identifier: GPL-2.0-or-later
namespace OpenPhysical.Biometrics.NFIQ2;

using Microsoft.Extensions.DependencyInjection;

/// <summary>Registers the NFIQ 2 image-quality engine.</summary>
public static class ServiceCollectionExtensions
{
    /// <summary>Registers a lazily initialized singleton quality engine.</summary>
    /// <param name="services">Application service registrations.</param>
    /// <returns>The same service collection for fluent registration.</returns>
    /// <exception cref="ArgumentNullException">The service collection is null.</exception>
    public static IServiceCollection AddNfiq2(this IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddSingleton<INfiq2Engine, Nfiq2Engine>();
        return services;
    }
}
