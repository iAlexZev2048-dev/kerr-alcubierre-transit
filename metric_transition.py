"""
Numerical reference: C^∞ bump function ψ(z) and Kerr → Alcubierre metric ramp
in the proper time τ of the co-moving frame (proof of concept / control loop simulation).
"""

from __future__ import annotations

import math
from typing import Callable, Sequence, TypeVar

T = TypeVar("T", float, list[float])


def psi(z: T) -> T:
    """C^∞ bump function: exp(-1/(1-z²)) for |z|<1, 0 for |z|>=1."""
    if isinstance(z, list):
        return [psi(x) for x in z]
    if abs(z) >= 1.0:
        return 0.0
    u = 1.0 - z * z
    return math.exp(-1.0 / u)


def psi_prime(z: T) -> T:
    """dψ/dz; zero outside of (-1, 1)."""
    if isinstance(z, list):
        return [psi_prime(x) for x in z]
    if abs(z) >= 1.0:
        return 0.0
    u = 1.0 - z * z
    return -2.0 * z * math.exp(-1.0 / u) / (u * u)


def z_phase(tau: float, tau_crit: float, delta_tau: float) -> float:
    return 2.0 * (tau - tau_crit) / delta_tau


def psi_tau(tau: float, tau_crit: float, delta_tau: float) -> float:
    return psi(z_phase(tau, tau_crit, delta_tau))


def dpsi_dtau(tau: float, tau_crit: float, delta_tau: float) -> float:
    z = z_phase(tau, tau_crit, delta_tau)
    return psi_prime(z) * (2.0 / delta_tau)


def blend_metric(
    g_kerr: Sequence[Sequence[float]],
    g_alc: Sequence[Sequence[float]],
    tau: float,
    tau_crit: float,
    delta_tau: float,
) -> list[list[float]]:
    """Linear component-wise blend: g_eff = ψ g_Kerr + (1-ψ) g_Alc."""
    w = psi_tau(tau, tau_crit, delta_tau)
    n = len(g_kerr)
    return [
        [w * g_kerr[i][j] + (1.0 - w) * g_alc[i][j] for j in range(n)]
        for i in range(n)
    ]


def det_4x4(m: Sequence[Sequence[float]]) -> float:
    """4×4 determinant by Laplace expansion (fixed chart)."""
    if len(m) != 4:
        raise ValueError("4×4 matrix required")

    def det3(a: list[list[float]]) -> float:
        return (
            a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
            - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
            + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
        )

    d = 0.0
    for j in range(4):
        minor = [[m[i][k] for k in range(4) if k != j] for i in range(1, 4)]
        sign = -1.0 if j % 2 else 1.0
        d += sign * m[0][j] * det3(minor)
    return d


def negative_energy_rate(
    tau: float,
    tau_crit: float,
    delta_tau: float,
    scale: float = 1.0,
) -> float:
    """Proxy: |dψ/dτ| proportional to the exotic ignition cost."""
    return scale * abs(dpsi_dtau(tau, tau_crit, delta_tau))


def suggest_delta_tau(
    z_dot_max: float,
    tau_dot: float = 1.0,
) -> float:
    """Minimum Δτ to maintain |dz/dτ| = 2|τ̇|/Δτ <= z_dot_max."""
    if z_dot_max <= 0:
        raise ValueError("z_dot_max must be positive")
    return 2.0 * abs(tau_dot) / z_dot_max
