"""
T_μν proxy from g_μν (linearized order / trace).
Does not replace numerical relativity; feeds the control loop with targets
consistent with the measured effective metric.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from engine_control import Tensor, blend_tensor
from metric_transition import det_4x4, psi_tau

Matrix4 = list[list[float]]
COUPLING = 1.0 / (8.0 * math.pi)  # 8πG, G=c=1


@dataclass
class EnergyConditions:
    """Violations of energy conditions (signs of ρ and trace)."""

    rho: float
    trace_P: float
    violates_WEC: bool
    violates_NEC: bool
    violates_SEC: bool


def minkowski_cartesian() -> Matrix4:
    return [
        [-1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def tensor_from_matrix(g: Matrix4) -> Tensor:
    """Extracts scalar proxy of T from perturbation h = g − η."""
    eta = minkowski_cartesian()
    h00 = g[0][0] - eta[0][0]
    hxx = g[1][1] - eta[1][1]
    hyy = g[2][2] - eta[2][2]
    hzz = g[3][3] - eta[3][3]
    htx = g[0][1] - eta[0][1]

    rho = -COUPLING * h00
    return Tensor(
        rho=rho,
        T_xx=COUPLING * hxx,
        T_yy=COUPLING * hyy,
        T_zz=COUPLING * hzz,
        T_tx=COUPLING * htx,
    )


def T_from_g(g: Matrix4) -> Tensor:
    return tensor_from_matrix(g)


def effective_T_from_blend(
    g_kerr: Matrix4,
    g_alc: Matrix4,
    tau: float,
    tau_crit: float,
    delta_tau: float,
) -> Tensor:
    w = psi_tau(tau, tau_crit, delta_tau)
    t_k = T_from_g(g_kerr)
    t_a = T_from_g(g_alc)
    return blend_tensor(w, t_k, t_a)


def energy_conditions(t: Tensor, n_timelike: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)) -> EnergyConditions:
    """Checks WEC/NEC/SEC in order of magnitude for the proxy."""
    nx, ny, nz = n_timelike[1], n_timelike[2], n_timelike[3]
    trace_P = t.T_xx + t.T_yy + t.T_zz
    nec = t.rho
    sec = t.rho + trace_P
    return EnergyConditions(
        rho=t.rho,
        trace_P=trace_P,
        violates_WEC=t.rho < 0,
        violates_NEC=nec < 0,
        violates_SEC=sec < 0,
    )


def curvature_proxy(g: Matrix4) -> float:
    """|R| ~ |det(g) − det(η)| as an operational curvature scalar."""
    return abs(det_4x4(g) + 1.0)
