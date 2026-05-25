"""
Operational detection of τ_crit (causal injection / local time inversion).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto

from engine_metrics import InjectionSite, metrics_in_local_chart
from metric_transition import det_4x4, z_phase


class CausalSignal(Enum):
    NORMAL = auto()
    ERGOSPHERE = auto()
    CLOSED_CONE = auto()
    TIME_INVERSION = auto()


@dataclass
class CausalState:
    signal: CausalSignal
    g_tt: float
    tangent_ds2: float
    clock_ratio: float
    det_g: float
    estimated_tau_crit: float | None


def g_tt_component(g: list[list[float]]) -> float:
    return g[0][0]


def tangent_temporal_ds2(g: list[list[float]], v_spatial: tuple[float, float, float] = (0.1, 0.0, 0.0)) -> float:
    """ds² for an approximate 4-velocity (1, v_x, v_y, v_z) normalized in order of magnitude."""
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


def clock_ratio_vs_minkowski(g: list[list[float]]) -> float:
    """√|g_tt / (−1)| — <1 dilation, >1 in ergosphere with g_tt>0."""
    gtt = g[0][0]
    return math.sqrt(abs(gtt))


def evaluate_causal_state(
    site: InjectionSite,
    tau: float,
    tau_crit: float,
    delta_tau: float,
    *,
    beacon_clock: float = 1.0,
    local_clock: float | None = None,
) -> CausalState:
    from engine_metrics import g_effective_at_tau

    g = g_effective_at_tau(site, tau, tau_crit, delta_tau)
    gtt = g_tt_component(g)
    ds2 = tangent_temporal_ds2(g)
    det = det_4x4(g)
    ratio = clock_ratio_vs_minkowski(g)

    if local_clock is not None and beacon_clock > 0:
        ratio = local_clock / beacon_clock

    signal = CausalSignal.NORMAL
    tau_est: float | None = None

    if gtt > 0:
        signal = CausalSignal.ERGOSPHERE
    if ds2 < 0:
        signal = CausalSignal.CLOSED_CONE
    if gtt > 0 and ds2 < 0:
        signal = CausalSignal.TIME_INVERSION
        tau_est = tau

    return CausalState(
        signal=signal,
        g_tt=gtt,
        tangent_ds2=ds2,
        clock_ratio=ratio,
        det_g=det,
        estimated_tau_crit=tau_est,
    )


def detect_tau_crit(
    site: InjectionSite,
    tau_grid: list[float],
    delta_tau: float,
    tau_crit_guess: float = 0.0,
) -> float:
    """
    First τ in the grid where TIME_INVERSION occurs; if none, the τ with maximum g_tt.
    """
    best_tau = tau_crit_guess
    best_gtt = -1e30
    for tau in tau_grid:
        st = evaluate_causal_state(site, tau, tau_crit_guess, delta_tau)
        if st.signal == CausalSignal.TIME_INVERSION:
            return tau
        if st.g_tt > best_gtt:
            best_gtt = st.g_tt
            best_tau = tau
    return best_tau
