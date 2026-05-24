"""
Detección operativa de τ_crit (inyección causal / inversión temporal local).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto

from metricas_motor import InjectionSite, metrics_in_ship_chart
from transicion_metrica import det_4x4, z_phase


class SenalCausal(Enum):
    NORMAL = auto()
    ERGOSFERA = auto()
    CONO_CERRADO = auto()
    INVERSION_TEMPORAL = auto()


@dataclass
class EstadoCausal:
    senal: SenalCausal
    g_tt: float
    ds2_tangente: float
    ratio_reloj: float
    det_g: float
    tau_crit_estimado: float | None


def g_tt_componente(g: list[list[float]]) -> float:
    return g[0][0]


def ds2_tangente_temporal(g: list[list[float]], v_spatial: tuple[float, float, float] = (0.1, 0.0, 0.0)) -> float:
    """ds² para 4-velocidad aproximada (1, v_x, v_y, v_z) normalizada en orden de magnitud."""
    vx, vy, vz = v_spatial
    return (
        g[0][0]
        + 2 * g[0][1] * vx
        + 2 * g[0][2] * vy
        + 2 * g[0][3] * vz
        + g[1][1] * vx * vx
        + g[2][2] * vy * vy
        + g[3][3] * vz * vz
    )


def ratio_reloj_vs_minkowski(g: list[list[float]]) -> float:
    """√|g_tt / (−1)| — <1 dilatación, >1 en ergósfera con g_tt>0."""
    gtt = g[0][0]
    return math.sqrt(abs(gtt))


def evaluar_estado_causal(
    site: InjectionSite,
    tau: float,
    tau_crit: float,
    delta_tau: float,
    *,
    reloj_beacon: float = 1.0,
    reloj_nave: float | None = None,
) -> EstadoCausal:
    from metricas_motor import g_effective_at_tau

    g = g_effective_at_tau(site, tau, tau_crit, delta_tau)
    gtt = g_tt_componente(g)
    ds2 = ds2_tangente_temporal(g)
    det = det_4x4(g)
    ratio = ratio_reloj_vs_minkowski(g)

    if reloj_nave is not None and reloj_beacon > 0:
        ratio = reloj_nave / reloj_beacon

    senal = SenalCausal.NORMAL
    tau_est: float | None = None

    if gtt > 0:
        senal = SenalCausal.ERGOSFERA
    if ds2 < 0:
        senal = SenalCausal.CONO_CERRADO
    if gtt > 0 and ds2 < 0:
        senal = SenalCausal.INVERSION_TEMPORAL
        tau_est = tau

    return EstadoCausal(
        senal=senal,
        g_tt=gtt,
        ds2_tangente=ds2,
        ratio_reloj=ratio,
        det_g=det,
        tau_crit_estimado=tau_est,
    )


def detectar_tau_crit(
    site: InjectionSite,
    tau_grid: list[float],
    delta_tau: float,
    tau_crit_guess: float = 0.0,
) -> float:
    """
    Primer τ en la malla donde aparece INVERSION_TEMPORAL; si no hay, el τ con g_tt máximo.
    """
    best_tau = tau_crit_guess
    best_gtt = -1e30
    for tau in tau_grid:
        st = evaluar_estado_causal(site, tau, tau_crit_guess, delta_tau)
        if st.senal == SenalCausal.INVERSION_TEMPORAL:
            return tau
        if st.g_tt > best_gtt:
            best_gtt = st.g_tt
            best_tau = tau
    return best_tau
