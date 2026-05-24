"""
Phase 3 — Adaptive PID loop for effective metric stabilization.
Translates ψ(z) and T_target into exotic injection, optical ring, and ballast commands.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from engine_metrics import InjectionSite, g_effective_at_tau
from metric_transition import (
    det_4x4,
    dpsi_dtau,
    psi,
    z_phase,
)

# --- operational constants ---------------------------------------------------

CRITICAL_HAWKING_LIMIT = 1.0e-3
Z_DIVERGENCE_LIMIT = 1.0e6
MIN_DET_G = 1.0e-12
DEFAULT_Z_COMPENSATION = 0.85
MIN_RANKING = 3.5


@dataclass
class Tensor:
    """T_μν proxy (principal components + frame-dragging coupling)."""

    rho: float = 0.0
    T_xx: float = 0.0
    T_yy: float = 0.0
    T_zz: float = 0.0
    T_tx: float = 0.0

    def __add__(self, other: Tensor) -> Tensor:
        return Tensor(
            self.rho + other.rho,
            self.T_xx + other.T_xx,
            self.T_yy + other.T_yy,
            self.T_zz + other.T_zz,
            self.T_tx + other.T_tx,
        )

    def __sub__(self, other: Tensor) -> Tensor:
        return Tensor(
            self.rho - other.rho,
            self.T_xx - other.T_xx,
            self.T_yy - other.T_yy,
            self.T_zz - other.T_zz,
            self.T_tx - other.T_tx,
        )

    def scale(self, s: float) -> Tensor:
        return Tensor(
            s * self.rho,
            s * self.T_xx,
            s * self.T_yy,
            s * self.T_zz,
            s * self.T_tx,
        )


def blend_tensor(psi_val: float, t_kerr: Tensor, t_alc: Tensor) -> Tensor:
    w = psi_val
    return t_kerr.scale(w) + t_alc.scale(1.0 - w)


def T_kerr_nominal() -> Tensor:
    return Tensor(rho=1.2e4, T_xx=4e3, T_yy=4e3, T_zz=8e3, T_tx=-1.5e3)


def T_alcubierre_nominal() -> Tensor:
    return Tensor(rho=-5e4, T_xx=-2e4, T_yy=-2e4, T_zz=-3e4, T_tx=0.0)


@dataclass
class ShipSensors:
    vacuum_fluctuation: float = 0.0
    scalar_curvature: float = 0.0
    det_g_eff: float = 1.0
    measured_T_zz: float = 0.0
    jacobian_ranking: float = 4.0


@dataclass
class PidGains:
    Kp: float = 2.0
    Ki: float = 0.4
    Kd: float = 0.15


class AdaptivePid:
    def __init__(self, gains: PidGains | None = None) -> None:
        self._g = gains or PidGains()
        self._integral = 0.0
        self._error_prev = 0.0
        self.Kp_eff = self._g.Kp
        self.Ki_eff = self._g.Ki
        self.Kd_eff = self._g.Kd

    def update_gains(self, dpsi_dtau: float, radiation_leak: float) -> None:
        ramp_scale = 1.0 + min(4.0, abs(dpsi_dtau) * 8.0)
        attenuation = 1.0 / (1.0 + 50.0 * radiation_leak)
        self.Kp_eff = self._g.Kp * ramp_scale * attenuation
        self.Ki_eff = self._g.Ki * ramp_scale * attenuation
        self.Kd_eff = self._g.Kd * ramp_scale

    def step(self, error: float, dt: float) -> float:
        if dt <= 0:
            return 0.0
        self._integral += error * dt
        deriv = (error - self._error_prev) / dt
        self._error_prev = error
        return self.Kp_eff * error + self.Ki_eff * self._integral + self.Kd_eff * deriv

    def reset(self) -> None:
        self._integral = 0.0
        self._error_prev = 0.0


@dataclass
class TransitionParameters:
    tau_crit: float = 0.0
    delta_tau: float = 2.0
    z_shape: float = 1.0
    dt_control: float = 1.0e-4


@dataclass
class ControlOutput:
    applied_injection: Tensor = field(default_factory=Tensor)
    ring_frequency_hz: float = 0.0
    ballast_rate_kg_s: float = 0.0
    emergency_rupture: bool = False
    z_compensation_mode: bool = False


def error_tensor(target: Tensor, measured: Tensor) -> float:
    e_rho = target.rho - measured.rho
    e_zz = target.T_zz - measured.T_zz
    return math.hypot(e_rho, e_zz)


def ring_frequency_from_psi(psi_val: float, f_base_hz: float = 1e9) -> float:
    p = max(0.0, min(1.0, psi_val))
    return f_base_hz * (0.05 + 0.95 * p)


def ballast_rate_from_dpsi(dpsi_dtau: float, gain: float = 1e2) -> float:
    return gain * abs(dpsi_dtau)


def adjust_orthogonal_axis(z_shape: float, factor: float = DEFAULT_Z_COMPENSATION) -> float:
    return z_shape * factor


def is_map_stable(s: ShipSensors) -> bool:
    return (
        abs(s.det_g_eff) > MIN_DET_G
        and s.jacobian_ranking >= MIN_RANKING
        and abs(s.measured_T_zz) < Z_DIVERGENCE_LIMIT
    )


def is_z_axis_diverging(s: ShipSensors) -> bool:
    return abs(s.measured_T_zz) >= Z_DIVERGENCE_LIMIT or abs(s.det_g_eff) < MIN_DET_G


def ranking_from_metric(g_eff: list[list[float]]) -> float:
    """
    F_* rank proxy: 4·|det(g_eff)|^(1/4) / tr(|g|).
    Drops if the map loses volume (spaghettification / degenerate chart).
    """
    det = abs(det_4x4(g_eff))
    tr = sum(abs(g_eff[i][j]) for i in range(4) for j in range(4))
    if tr < 1e-30:
        return 0.0
    return 4.0 * (det ** 0.25) / tr


def sensors_from_metric(
    site: InjectionSite,
    tau: float,
    par: TransitionParameters,
    *,
    vacuum_fluctuation: float = 0.0,
    measured_T_zz: float = 0.0,
) -> ShipSensors:
    g_eff = g_effective_at_tau(site, tau, par.tau_crit, par.delta_tau)
    return ShipSensors(
        vacuum_fluctuation=vacuum_fluctuation,
        det_g_eff=det_4x4(g_eff),
        measured_T_zz=measured_T_zz,
        jacobian_ranking=ranking_from_metric(g_eff),
    )


def control_metric_transition(
    z_pos: float,
    t_actual: float,
    sensors: ShipSensors,
    T_measured: Tensor,
    pid: AdaptivePid,
    par: TransitionParameters,
    T_kerr: Tensor | None = None,
    T_alc: Tensor | None = None,
) -> ControlOutput:
    """
    Phase 3 core — equivalent to the C++ pseudocode in the design document.
    """
    out = ControlOutput()
    t_k = T_kerr if T_kerr is not None else T_kerr_nominal()
    t_a = T_alc if T_alc is not None else T_alcubierre_nominal()
    z_shape = par.z_shape

    psi_val = psi(z_pos)
    dpsi = dpsi_dtau(t_actual, par.tau_crit, par.delta_tau)

    T_target = blend_tensor(psi_val, t_k, t_a)
    T_target.T_zz *= z_shape

    out.ring_frequency_hz = ring_frequency_from_psi(psi_val)
    out.ballast_rate_kg_s = ballast_rate_from_dpsi(dpsi)

    if is_z_axis_diverging(sensors) or not is_map_stable(sensors):
        out.emergency_rupture = True
        T_target = t_a
        z_shape = DEFAULT_Z_COMPENSATION

    radiation_leak = sensors.vacuum_fluctuation
    pid.update_gains(dpsi, radiation_leak)

    injection = T_target

    if radiation_leak > CRITICAL_HAWKING_LIMIT:
        out.z_compensation_mode = True
        z_shape = adjust_orthogonal_axis(z_shape)
        T_target.T_zz *= z_shape
        compensation = Tensor(
            rho=radiation_leak * 1e5,
            T_zz=radiation_leak * 5e4,
        )
        injection = T_target - compensation

    err = error_tensor(injection, T_measured)
    u_pid = pid.step(err, par.dt_control)
    injection.rho -= u_pid

    out.applied_injection = injection
    return out


def simulate_phase3(
    n_steps: int = 41,
    site: InjectionSite | None = None,
) -> list[dict[str, float | bool | str]]:
    site = site or InjectionSite()
    par = TransitionParameters()
    pid = AdaptivePid()
    T_measured = T_kerr_nominal()
    log: list[dict[str, float | bool | str]] = []

    for i in range(n_steps):
        tau = par.tau_crit + (i / (n_steps - 1) - 0.5) * par.delta_tau if n_steps > 1 else par.tau_crit
        z = z_phase(tau, par.tau_crit, par.delta_tau)
        hawking = 1.5e-3 if abs(z) < 0.05 else 2e-4
        sensors = sensors_from_metric(
            site, tau, par, vacuum_fluctuation=hawking, measured_T_zz=T_measured.T_zz
        )
        out = control_metric_transition(z, tau, sensors, T_measured, pid, par)
        T_measured.rho += 0.3 * (out.applied_injection.rho - T_measured.rho)
        log.append(
            {
                "tau": tau,
                "z": z,
                "psi": psi(z),
                "det_g_eff": sensors.det_g_eff,
                "ranking": sensors.jacobian_ranking,
                "f_GHz": out.ring_frequency_hz / 1e9,
                "lastre_kg_s": out.ballast_rate_kg_s,
                "rho_cmd": out.applied_injection.rho,
                "emergencia": out.emergency_rupture,
                "comp_Z": out.z_compensation_mode,
            }
        )
    return log


def print_simulation(log: list[dict[str, float | bool | str]]) -> None:
    print("=== Phase 3 — Adaptive PID + ψ(z) ===")
    print("tau      z      psi    det(g)   rank   f_GHz  ballast  rho_cmd  emerg")
    for row in log:
        em = "YES" if row["emergencia"] else "no"
        print(
            f"{row['tau']:6.3f} {row['z']:6.3f} {row['psi']:6.4f} "
            f"{row['det_g_eff']:9.2e} {row['ranking']:5.3f} "
            f"{row['f_GHz']:6.3f} {row['lastre_kg_s']:7.2f} "
            f"{row['rho_cmd']:9.1f} {em}"
        )


if __name__ == "__main__":
    print_simulation(simulate_phase3())
