"""
Proxy de T_μν a partir de g_μν (orden linealizado / traza).
No sustituye relatividad numérica; alimenta el lazo de control con objetivos
coherentes con la métrica efectiva medida.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from control_motor import Tensor, blend_tensor
from transicion_metrica import det_4x4, psi_tau

Matrix4 = list[list[float]]
COUPLING = 1.0 / (8.0 * math.pi)  # 8πG, G=c=1


@dataclass
class CondicionesEnergia:
    """Violaciones de condiciones de energía (signos de ρ y traza)."""

    rho: float
    traza_P: float
    viola_WEC: bool
    viola_NEC: bool
    viola_SEC: bool


def minkowski_cart() -> Matrix4:
    return [
        [-1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def tensor_from_matrix(g: Matrix4) -> Tensor:
    """Extrae proxy escalar de T desde perturbación h = g − η."""
    eta = minkowski_cart()
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


def T_efectivo_desde_mezcla(
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


def condiciones_energia(t: Tensor, n_timelike: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)) -> CondicionesEnergia:
    """Comprueba WEC/NEC/SEC en orden de magnitud para el proxy."""
    nx, ny, nz = n_timelike[1], n_timelike[2], n_timelike[3]
    traza_P = t.T_xx + t.T_yy + t.T_zz
    nec = t.rho
    sec = t.rho + traza_P
    return CondicionesEnergia(
        rho=t.rho,
        traza_P=traza_P,
        viola_WEC=t.rho < 0,
        viola_NEC=nec < 0,
        viola_SEC=sec < 0,
    )


def curvatura_proxy(g: Matrix4) -> float:
    """|R| ~ |det(g) − det(η)| como escalar operativo de curvatura."""
    return abs(det_4x4(g) + 1.0)
