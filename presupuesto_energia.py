"""
Presupuesto energético: Penrose (Fase 2) vs ignición Alcubierre (Fase 3).
Unidades geométricas G = c = 1 salvo etiquetas SI opcionales.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from metricas_motor import InjectionSite, kerr_outer_horizon
from transicion_metrica import dpsi_dtau, psi_prime, z_phase


@dataclass
class PresupuestoEnergia:
    masa_bh: float
    spin: float
    r_inyeccion: float
    eta_penrose: float
    E_penrose_max: float
    E_alcubierre_estatica: float
    E_pico_rampa: float
    ratio_pico_penrose: float
    viable: bool
    notas: str


def eficiencia_penrose(spin: float) -> float:
    """
    Cota orientativa de extracción (Kerr extremo a ~20–29%).
    η ≈ 1 − √(1 − a²/(a²+1)) para a/M → 1.
    """
    a = abs(spin)
    if a >= 1.0:
        return 0.29
    return 1.0 - math.sqrt(max(0.0, 1.0 - (a * a) / (a * a + 1.0)))


def energia_alcubierre_burbuja(vs: float, radius: float, sigma: float) -> float:
    """
    Orden de magnitud (Alcubierre 1994, unidades relativistas):
    E ~ v_s² R² / (8π σ²) en unidades donde c=G=1.
    """
    if sigma <= 0 or radius <= 0:
        return float("inf")
    return (vs * vs) * (radius ** 2) / (8.0 * math.pi * sigma * sigma)


def energia_pico_rampa(
    tau: float,
    tau_crit: float,
    delta_tau: float,
    escala: float = 1.0,
) -> float:
    z = z_phase(tau, tau_crit, delta_tau)
    return escala * abs(psi_prime(z) * (2.0 / delta_tau))


def evaluar_presupuesto(
    site: InjectionSite | None = None,
    tau_crit: float = 0.0,
    delta_tau: float = 2.0,
    masa_nave: float = 1.0e-3,
) -> PresupuestoEnergia:
    site = site or InjectionSite()
    m = site.mass
    eta = eficiencia_penrose(site.spin)
    e_penrose = eta * m * masa_nave
    e_alc = energia_alcubierre_burbuja(site.vs, site.bubble_radius, site.sigma)
    e_pico = energia_pico_rampa(tau_crit, tau_crit, delta_tau, escala=e_alc * 0.1)
    ratio = e_pico / e_penrose if e_penrose > 0 else float("inf")
    viable = e_pico < e_penrose * 5.0 and e_alc < m * 1.0e4
    notas = (
        f"eta_Penrose~{eta:.3f}; pico rampa en tau=tau_crit; "
        f"si ratio_pico_penrose>>1 reducir delta_tau o v_s."
    )
    return PresupuestoEnergia(
        masa_bh=m,
        spin=site.spin,
        r_inyeccion=site.r,
        eta_penrose=eta,
        E_penrose_max=e_penrose,
        E_alcubierre_estatica=e_alc,
        E_pico_rampa=e_pico,
        ratio_pico_penrose=ratio,
        viable=viable,
        notas=notas,
    )


def tabla_presupuesto_texto(pb: PresupuestoEnergia) -> str:
    lines = [
        "=== Presupuesto energetico (G=c=1) ===",
        f"  M_BH          = {pb.masa_bh}",
        f"  a/M           = {pb.spin}",
        f"  r_inyeccion   = {pb.r_inyeccion:.6f}  (r_plus={kerr_outer_horizon(pb.masa_bh, pb.spin):.6f})",
        f"  eta_Penrose   = {pb.eta_penrose:.4f}",
        f"  E_Penrose_max = {pb.E_penrose_max:.6e}",
        f"  E_Alc_estatic.  = {pb.E_alcubierre_estatica:.6e}",
        f"  E_pico dpsi   = {pb.E_pico_rampa:.6e}",
        f"  ratio pico/P  = {pb.ratio_pico_penrose:.4f}",
        f"  viable (PoC)  = {pb.viable}",
        f"  -> {pb.notas}",
    ]
    return "\n".join(lines)
