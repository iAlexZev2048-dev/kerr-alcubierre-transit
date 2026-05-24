"""
Métricas explícitas Kerr (Boyer–Lindquist) y Alcubierre en chart común (t, x, y, z)
del marco co-móvil de la Nave B, más barrido de det(g_eff) durante la rampa ψ.
Unidades geométricas: G = c = 1.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from transicion_metrica import blend_metric, det_4x4, psi_tau

Matrix4 = list[list[float]]


# --- álgebra lineal 4×4 -------------------------------------------------------

def mat_transpose(m: Matrix4) -> Matrix4:
    return [[m[j][i] for j in range(4)] for i in range(4)]


def mat_mul(a: Matrix4, b: Matrix4) -> Matrix4:
    return [
        [sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)]
        for i in range(4)
    ]


def mat_inv(m: Matrix4, eps: float = 1e-12) -> Matrix4:
    """Inversa por eliminación de Gauss–Jordan."""
    n = 4
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        pivot = max(range(n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < eps:
            raise ValueError("matriz singular")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        div = aug[col][col]
        aug[col] = [v / div for v in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [aug[row][k] - factor * aug[col][k] for k in range(2 * n)]
    return [row[n:] for row in aug]


def transform_metric_covariant(g: Matrix4, jacobian: Matrix4) -> Matrix4:
    """
    g'_αβ = (J⁻¹)^μ_α g_μν (J⁻¹)^ν_β  con y^α = J^α_μ x^μ (linealizado en el punto).
  """
    j_inv = mat_inv(jacobian)
    j_inv_t = mat_transpose(j_inv)
    return mat_mul(mat_mul(j_inv_t, g), j_inv)


def apply_block_rotation(g: Matrix4, rot3: list[list[float]]) -> Matrix4:
    """R₄ = diag(1, R); g' = R₄ᵀ g R₄ (rotación espacial ortogonal)."""
    r4 = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, rot3[0][0], rot3[0][1], rot3[0][2]],
        [0.0, rot3[1][0], rot3[1][1], rot3[1][2]],
        [0.0, rot3[2][0], rot3[2][1], rot3[2][2]],
    ]
    rt = mat_transpose(r4)
    return mat_mul(mat_mul(rt, g), r4)


# --- Kerr (Boyer–Lindquist) ---------------------------------------------------

def kerr_boyer_lindquist(
    r: float,
    theta: float,
    *,
    mass: float,
    spin: float,
) -> Matrix4:
    """
    Orden de coordenadas: (t, r, θ, φ).
    rs = 2M; Δ = r² − rs r + a²; ρ² = r² + a² cos²θ.
    """
    rs = 2.0 * mass
    a = spin
    rho2 = r * r + a * a * math.cos(theta) ** 2
    delta = r * r - rs * r + a * a
    sin2 = math.sin(theta) ** 2

    g_tt = -(1.0 - rs * r / rho2)
    g_rr = rho2 / delta
    g_thth = rho2
    g_phph = (r * r + a * a + rs * r * a * a * sin2 / rho2) * sin2
    g_tph = -rs * r * a * sin2 / rho2

    return [
        [g_tt, 0.0, 0.0, g_tph],
        [0.0, g_rr, 0.0, 0.0],
        [0.0, 0.0, g_thth, 0.0],
        [g_tph, 0.0, 0.0, g_phph],
    ]


def jacobian_bl_to_cartesian(r: float, theta: float, phi: float) -> Matrix4:
    """
    (t, r, θ, φ) → (t, x, y, z) con x = r sinθ cosφ, y = r sinθ sinφ, z = r cosθ.
    """
    st, ct = math.sin(theta), math.cos(theta)
    sp, cp = math.sin(phi), math.cos(phi)

    dx_dr = st * cp
    dx_dth = r * ct * cp
    dx_dph = -r * st * sp

    dy_dr = st * sp
    dy_dth = r * ct * sp
    dy_dph = r * st * cp

    dz_dr = ct
    dz_dth = -r * st
    dz_dph = 0.0

    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, dx_dr, dx_dth, dx_dph],
        [0.0, dy_dr, dy_dth, dy_dph],
        [0.0, dz_dr, dz_dth, dz_dph],
    ]


def kerr_outer_horizon(mass: float, spin: float) -> float:
    a = spin
    return mass + math.sqrt(mass * mass - a * a)


# --- Alcubierre (chart co-móvil) ----------------------------------------------

def alcubierre_shape(xi: float, sigma: float, radius: float) -> float:
    """f(ξ) de Alcubierre (1994), normalizado con f(0) ≈ 1 en el centro."""
    num = math.tanh(sigma * (xi + radius)) - math.tanh(sigma * (xi - radius))
    den = 2.0 * math.tanh(sigma * radius)
    return num / den


def alcubierre_cartesian(
    vs: float,
    sigma: float,
    radius: float,
    *,
    xi_center: float = 0.0,
) -> Matrix4:
    """
    ds² = −dt² + (dx − v_s f dt)² + dy² + dz²; orden (t, x, y, z).
    """
    f = alcubierre_shape(xi_center, sigma, radius)
    g_tt = -1.0 + vs * vs * f * f
    g_tx = -vs * f
    return [
        [g_tt, g_tx, 0.0, 0.0],
        [g_tx, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def rotation_y(angle: float) -> list[list[float]]:
    c, s = math.cos(angle), math.sin(angle)
    return [
        [c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c],
    ]


def rotation_z(angle: float) -> list[list[float]]:
    c, s = math.cos(angle), math.sin(angle)
    return [
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0],
    ]


# --- sitio de inyección (ergósfera) -------------------------------------------

@dataclass(frozen=True)
class InjectionSite:
    """Punto de acoplamiento Kerr → Alcubierre en la ergósfera ecuatorial."""

    mass: float = 1.0
    spin: float = 0.998
    r_factor: float = 1.05  # r = r_factor × r₊
    theta: float = math.pi / 2
    phi: float = 0.0
    # Alcubierre
    vs: float = 0.5
    sigma: float = 1.0
    bubble_radius: float = 1.0
    # Alinear eje x de la burbuja con ∂/∂φ (arrastre) en el ecuador
    align_bubble_with_frame_drag: bool = True

    @property
    def r(self) -> float:
        return self.r_factor * kerr_outer_horizon(self.mass, self.spin)


def metrics_in_ship_chart(site: InjectionSite) -> tuple[Matrix4, Matrix4]:
    """
    Devuelve (g_Kerr, g_Alc) en coordenadas (t, x, y, z) del marco co-móvil.
    """
    g_bl = kerr_boyer_lindquist(site.r, site.theta, mass=site.mass, spin=site.spin)
    j = jacobian_bl_to_cartesian(site.r, site.theta, site.phi)
    g_kerr = transform_metric_covariant(g_bl, j)

    g_alc = alcubierre_cartesian(
        site.vs, site.sigma, site.bubble_radius, xi_center=0.0
    )
    if site.align_bubble_with_frame_drag:
        # En φ=0, θ=π/2: ∂/∂φ ∥ ê_y; eje x de Alcubierre → y cartesiano (rotación −π/2 en z).
        g_alc = apply_block_rotation(g_alc, rotation_z(-math.pi / 2))

    return g_kerr, g_alc


def g_effective_at_tau(
    site: InjectionSite,
    tau: float,
    tau_crit: float,
    delta_tau: float,
) -> Matrix4:
    g_k, g_a = metrics_in_ship_chart(site)
    return blend_metric(g_k, g_a, tau, tau_crit, delta_tau)


# --- barrido det(g_eff) -------------------------------------------------------

@dataclass
class SweepSample:
    tau: float
    tau_crit: float
    delta_tau: float
    psi: float
    det_g_eff: float
    det_g_kerr: float
    det_g_alc: float


def sweep_transition(
    site: InjectionSite,
    tau_grid: Iterable[float],
    delta_tau_values: Iterable[float],
    tau_crit: float = 0.0,
) -> Iterator[SweepSample]:
    g_k, g_a = metrics_in_ship_chart(site)
    det_k = det_4x4(g_k)
    det_a = det_4x4(g_a)
    for dtau in delta_tau_values:
        for tau in tau_grid:
            w = psi_tau(tau, tau_crit, dtau)
            g_eff = blend_metric(g_k, g_a, tau, tau_crit, dtau)
            yield SweepSample(
                tau=tau,
                tau_crit=tau_crit,
                delta_tau=dtau,
                psi=w,
                det_g_eff=det_4x4(g_eff),
                det_g_kerr=det_k,
                det_g_alc=det_a,
            )


def summarize_sweep(samples: Sequence[SweepSample]) -> dict[str, float | int | bool]:
    dets = [s.det_g_eff for s in samples]
    min_det = min(dets)
    max_det = max(dets)
    signs = {1 if d > 0 else (-1 if d < 0 else 0) for d in dets}
    return {
        "n_samples": len(samples),
        "min_det": min_det,
        "max_det": max_det,
        "all_nonzero": all(abs(d) > 1e-30 for d in dets),
        "sign_changes": len(signs) > 1,
        "min_abs_det": min(abs(d) for d in dets),
    }


def write_sweep_csv(path: Path, samples: Iterable[SweepSample]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(samples)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "tau",
                "tau_crit",
                "delta_tau",
                "psi",
                "det_g_eff",
                "det_g_kerr",
                "det_g_alc",
            ]
        )
        for s in rows:
            w.writerow(
                [
                    s.tau,
                    s.tau_crit,
                    s.delta_tau,
                    s.psi,
                    s.det_g_eff,
                    s.det_g_kerr,
                    s.det_g_alc,
                ]
            )
    return len(rows)


def default_tau_grid(tau_crit: float, delta_tau: float, n: int = 41) -> list[float]:
    half = delta_tau
    step = (2.0 * half) / (n - 1) if n > 1 else 0.0
    return [tau_crit - half + i * step for i in range(n)]


def run_default_sweep(output: Path | None = None) -> dict[str, object]:
    site = InjectionSite()
    tau_crit = 0.0
    delta_values = [0.5, 1.0, 2.0, 4.0]
    all_samples: list[SweepSample] = []
    for dtau in delta_values:
        grid = default_tau_grid(tau_crit, dtau, n=41)
        all_samples.extend(sweep_transition(site, grid, [dtau], tau_crit=tau_crit))

    summary = summarize_sweep(all_samples)
    g_k, g_a = metrics_in_ship_chart(site)
    report: dict[str, object] = {
        "site": {
            "r": site.r,
            "theta": site.theta,
            "phi": site.phi,
            "mass": site.mass,
            "spin": site.spin,
            "vs": site.vs,
            "sigma": site.sigma,
            "bubble_radius": site.bubble_radius,
        },
        "det_g_kerr_cart": det_4x4(g_k),
        "det_g_alc_cart": det_4x4(g_a),
        "summary": summary,
    }

    if output is None:
        output = Path(__file__).resolve().parent / "sweep_det_results.csv"
    report["csv_rows"] = write_sweep_csv(output, all_samples)
    report["csv_path"] = str(output)
    return report


def print_report(report: dict[str, object]) -> None:
    site = report["site"]
    assert isinstance(site, dict)
    print("=== Metricas en chart (t, x, y, z) - Nave B ===")
    print(f"  r = {site['r']:.6f}  (factor {InjectionSite().r_factor} x r_plus)")
    print(f"  theta = {site['theta']:.4f} rad,  phi = {site['phi']:.4f} rad")
    print(f"  M = {site['mass']},  a = {site['spin']}")
    print(
        f"  Alcubierre: v_s = {site['vs']}, sigma = {site['sigma']}, R = {site['bubble_radius']}"
    )
    print(f"  det(g_Kerr)_cart = {report['det_g_kerr_cart']:.6e}")
    print(f"  det(g_Alc)_cart   = {report['det_g_alc_cart']:.6e}")
    sm = report["summary"]
    assert isinstance(sm, dict)
    print("=== Barrido psi(tau), delta_tau en {0.5, 1, 2, 4} ===")
    print(f"  muestras: {sm['n_samples']}")
    print(f"  min det(g_eff)     = {sm['min_det']:.6e}")
    print(f"  max det(g_eff)     = {sm['max_det']:.6e}")
    print(f"  min |det(g_eff)|   = {sm['min_abs_det']:.6e}")
    print(f"  todos distintos de 0: {sm['all_nonzero']}")
    print(f"  cambio de signo:      {sm['sign_changes']}")
    print(f"  CSV: {report['csv_path']} ({report['csv_rows']} filas)")


if __name__ == "__main__":
    print_report(run_default_sweep())
