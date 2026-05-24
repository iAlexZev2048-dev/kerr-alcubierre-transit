"""
State machine Phase 0 → 3 for the causal engine (Ship A / Ship B).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from engine_control import (
    AdaptivePid,
    TransitionParameters,
    ControlOutput,
    ShipSensors,
    Tensor,
    control_metric_transition,
)
from einstein_proxy import T_from_g
from engine_metrics import InjectionSite, metrics_in_ship_chart
from energy_budget import evaluate_budget
from engine_control import ballast_rate_from_dpsi, ring_frequency_from_psi
from tau_crit import CausalSignal, detect_tau_crit, evaluate_causal_state
from metric_transition import dpsi_dtau, psi, z_phase


class Phase(Enum):
    CALIBRATION = auto()         # Phase 0 — Ship A, Minkowski
    DESCENT = auto()             # Phase 1 — passive ergosphere
    CTC_INJECTION = auto()       # Phase 2 — rings + Penrose
    TOPOLOGICAL_RUPTURE = auto() # Phase 3 — ψ-ramp
    EXTRACTION = auto()          # post-bubble, return to beacon
    ABORT = auto()


@dataclass
class ShipATelemetry:
    beacon_clock: float = 1.0
    link_active: bool = True
    coordinates_ok: bool = True


@dataclass
class EngineCommand:
    phase: Phase
    ring_frequency_hz: float = 0.0
    ballast_rate_kg_s: float = 0.0
    injection: Tensor = field(default_factory=Tensor)
    emergency_rupture: bool = False
    z_compensation_mode: bool = False
    message: str = ""


@dataclass
class EngineConfig:
    site: InjectionSite = field(default_factory=InjectionSite)
    par: TransitionParameters = field(default_factory=TransitionParameters)
    use_T_from_g: bool = True
    auto_tau_crit: bool = True


class CausalEngine:
    def __init__(self, config: EngineConfig | None = None) -> None:
        self.cfg = config or EngineConfig()
        self.phase = Phase.CALIBRATION
        self.pid = AdaptivePid()
        self.tau_crit_locked: float | None = None
        self.measured_T = Tensor()
        self._steps = 0
        self._beacon = ShipATelemetry()

    def set_beacon(self, beacon: ShipATelemetry) -> None:
        self._beacon = beacon

    def _tau_crit(self) -> float:
        return self.tau_crit_locked if self.tau_crit_locked is not None else self.cfg.par.tau_crit

    def transition(self, new_phase: Phase, msg: str = "") -> None:
        self.phase = new_phase
        self._last_msg = msg

    def step(self, tau: float, sensors: ShipSensors | None = None) -> EngineCommand:
        self._steps += 1
        site = self.cfg.site
        par = self.cfg.par
        z = z_phase(tau, self._tau_crit(), par.delta_tau)
        causal = evaluate_causal_state(site, tau, self._tau_crit(), par.delta_tau)

        if sensors is None:
            from engine_control import sensors_from_metric

            sensors = sensors_from_metric(site, tau, par)

        cmd = EngineCommand(phase=self.phase)

        # --- Phase 0: Calibration with Ship A ---
        if self.phase == Phase.CALIBRATION:
            if not self._beacon.link_active or not self._beacon.coordinates_ok:
                self.transition(Phase.ABORT, "loss of Ship A beacon")
            elif self._steps >= 1 and tau > par.tau_crit - 1.5 * par.delta_tau:
                self.transition(Phase.DESCENT, "beacon OK, starting descent")
            cmd.message = "synchronizing clock with Ship A"
            cmd.ring_frequency_hz = 0.0
            return self._finalize(cmd)

        # --- Phase 1: Passive Descent ---
        if self.phase == Phase.DESCENT:
            if causal.signal in (CausalSignal.ERGOSPHERE, CausalSignal.CLOSED_CONE):
                self.transition(Phase.CTC_INJECTION, "ergosphere reached")
            cmd.message = "main propulsion turned off"
            return self._finalize(cmd)

        # --- Phase 2: CTC + Penrose ---
        if self.phase == Phase.CTC_INJECTION:
            dpsi = dpsi_dtau(tau, self._tau_crit(), par.delta_tau)
            cmd.ballast_rate_kg_s = ballast_rate_from_dpsi(dpsi)
            cmd.ring_frequency_hz = ring_frequency_from_psi(psi(z))
            if self.cfg.auto_tau_crit and causal.signal == CausalSignal.TIME_INVERSION:
                self.tau_crit_locked = tau
                self.transition(Phase.TOPOLOGICAL_RUPTURE, f"tau_crit detected at tau={tau:.4f}")
            elif tau >= self._tau_crit():
                self.transition(
                    Phase.TOPOLOGICAL_RUPTURE,
                    f"programmed handover at tau_crit={self._tau_crit():.4f}",
                )
            pb = evaluate_budget(site, self._tau_crit(), par.delta_tau)
            if not pb.viable and self._steps > 5:
                self.transition(Phase.ABORT, "energy budget not viable")
            cmd.message = f"Penrose ballast={cmd.ballast_rate_kg_s:.2f} kg/s"
            if self.phase == Phase.TOPOLOGICAL_RUPTURE:
                pass  # fall through to Phase 3 block in the same step
            else:
                return self._finalize(cmd)

        # --- Phase 3 / Extraction: ψ control + PID ---
        if self.phase in (Phase.TOPOLOGICAL_RUPTURE, Phase.EXTRACTION):
            g_k, g_a = metrics_in_ship_chart(site)
            if self.cfg.use_T_from_g:
                t_k, t_a = T_from_g(g_k), T_from_g(g_a)
            else:
                from engine_control import T_alcubierre_nominal, T_kerr_nominal

                t_k, t_a = T_kerr_nominal(), T_alcubierre_nominal()

            out: ControlOutput = control_metric_transition(
                z, tau, sensors, self.measured_T, self.pid, par, t_k, t_a
            )
            self.measured_T.rho += 0.25 * (out.applied_injection.rho - self.measured_T.rho)

            cmd.ring_frequency_hz = out.ring_frequency_hz
            cmd.ballast_rate_kg_s = out.ballast_rate_kg_s
            cmd.injection = out.applied_injection
            cmd.emergency_rupture = out.emergency_rupture
            cmd.z_compensation_mode = out.z_compensation_mode

            if self.phase == Phase.TOPOLOGICAL_RUPTURE and abs(z) >= 1.0:
                self.transition(Phase.EXTRACTION, "ψ-ramp completed")
            cmd.message = f"ψ control z={z:.3f} signal={causal.signal.name}"

        if self.phase == Phase.ABORT:
            cmd.message = "ABORT — Alcubierre shield forced"
            cmd.emergency_rupture = True

        return self._finalize(cmd)

    def _finalize(self, cmd: EngineCommand) -> EngineCommand:
        cmd.phase = self.phase
        return cmd

    def calibrate_tau_crit(self, tau_grid: list[float]) -> float:
        tc = detect_tau_crit(
            self.cfg.site, tau_grid, self.cfg.par.delta_tau, self.cfg.par.tau_crit
        )
        self.tau_crit_locked = tc
        self.cfg.par.tau_crit = tc
        return tc
