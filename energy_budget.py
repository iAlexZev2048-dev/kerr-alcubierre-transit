"""
Energy budget: Penrose (Phase 2) vs Alcubierre ignition (Phase 3).
Geometrized units G = c = 1 unless optional SI labels are used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine_metrics import InjectionSite, kerr_outer_horizon
from metric_transition import dpsi_dtau, psi_prime, z_phase


@dataclass
class EnergyBudget:
    bh_mass: float
    spin: float
    r_injection: float
    penrose_efficiency: float
    max_penrose_energy: float
    static_alcubierre_energy: float
    peak_ramp_energy: float
    peak_to_penrose_ratio: float
    viable: bool
    notes: str


def penrose_efficiency(spin: float) -> float:
    """
    Guideline extraction limit (extreme Kerr to ~20–29%).
    η ≈ 1 − √(1 − a²/(a²+1)) as a/M → 1.
    """
    a = abs(spin)
    if a >= 1.0:
        return 0.29
    return 1.0 - math.sqrt(max(0.0, 1.0 - (a * a) / (a * a + 1.0)))


def alcubierre_bubble_energy(vs: float, radius: float, sigma: float) -> float:
    """
    Order of magnitude (Alcubierre 1994, relativistic units):
    E ~ v_s² R² / (8π σ²) in units where c=G=1.
    """
    if sigma <= 0 or radius <= 0:
        return float("inf")
    return (vs * vs) * (radius ** 2) / (8.0 * math.pi * sigma * sigma)


def peak_ramp_energy(
    tau: float,
    tau_crit: float,
    delta_tau: float,
    scale: float = 1.0,
) -> float:
    z = z_phase(tau, tau_crit, delta_tau)
    return scale * abs(psi_prime(z) * (2.0 / delta_tau))


def evaluate_budget(
    site: InjectionSite | None = None,
    tau_crit: float = 0.0,
    delta_tau: float = 2.0,
    ship_mass: float = 1.0e-3,
) -> EnergyBudget:
    site = site or InjectionSite()
    m = site.mass
    eta = penrose_efficiency(site.spin)
    e_penrose = eta * m * ship_mass
    e_alc = alcubierre_bubble_energy(site.vs, site.bubble_radius, site.sigma)
    e_pico = peak_ramp_energy(tau_crit, tau_crit, delta_tau, scale=e_alc * 0.1)
    ratio = e_pico / e_penrose if e_penrose > 0 else float("inf")
    viable = e_pico < e_penrose * 5.0 and e_alc < m * 1.0e4
    notes = (
        f"eta_Penrose~{eta:.3f}; peak ramp at tau=tau_crit; "
        f"if peak_to_penrose_ratio>>1, reduce delta_tau or v_s."
    )
    return EnergyBudget(
        bh_mass=m,
        spin=site.spin,
        r_injection=site.r,
        penrose_efficiency=eta,
        max_penrose_energy=e_penrose,
        static_alcubierre_energy=e_alc,
        peak_ramp_energy=e_pico,
        peak_to_penrose_ratio=ratio,
        viable=viable,
        notes=notes,
    )


def budget_table_text(pb: EnergyBudget) -> str:
    lines = [
        "=== Energy Budget (G=c=1) ===",
        f"  M_BH          = {pb.bh_mass}",
        f"  a/M           = {pb.spin}",
        f"  r_injection   = {pb.r_injection:.6f}  (r_plus={kerr_outer_horizon(pb.bh_mass, pb.spin):.6f})",
        f"  eta_Penrose   = {pb.penrose_efficiency:.4f}",
        f"  E_Penrose_max = {pb.max_penrose_energy:.6e}",
        f"  E_Alc_static  = {pb.static_alcubierre_energy:.6e}",
        f"  E_peak_dpsi   = {pb.peak_ramp_energy:.6e}",
        f"  ratio peak/P  = {pb.peak_to_penrose_ratio:.4f}",
        f"  viable (PoC)  = {pb.viable}",
        f"  -> {pb.notes}",
    ]
    return "\n".join(lines)
