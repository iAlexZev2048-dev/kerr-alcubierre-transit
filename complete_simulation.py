"""
Chained Phase 0 → 3 simulation with CSV telemetry and prior calibration.
"""

from __future__ import annotations

import csv
from pathlib import Path

from calibration import load_config, run_calibration
from engine_phases import EngineConfig, Phase, CausalEngine, ShipATelemetry
from engine_metrics import InjectionSite, default_tau_grid
from energy_budget import evaluate_budget, budget_table_text
from tau_crit import evaluate_causal_state

ROOT = Path(__file__).resolve().parent
LOG_CSV = ROOT / "complete_simulation.csv"


def simulate(
    n_tau: int = 61,
    delta_tau: float = 2.0,
    calibrate: bool = True,
) -> list[dict]:
    if calibrate:
        run_calibration(regenerate=False)
    elif load_config():
        from calibration import apply_to_control, load_config

        u = load_config()
        if u:
            apply_to_control(u)

    site = InjectionSite()
    cfg = EngineConfig(site=site)
    cfg.par.delta_tau = delta_tau
    motor = CausalEngine(cfg)
    motor.set_beacon(ShipATelemetry(beacon_clock=1.0, link_active=True))

    tau_grid = default_tau_grid(0.0, delta_tau * 1.5, n_tau)
    cfg.par.dt_control = tau_grid[1] - tau_grid[0]
    motor.calibrate_tau_crit(tau_grid)

    pb = evaluate_budget(site, motor._tau_crit(), delta_tau)
    print(budget_table_text(pb))
    print(f"\ncalibrated tau_crit = {motor._tau_crit():.6f}\n")

    log: list[dict] = []
    for tau in tau_grid:
        causal = evaluate_causal_state(site, tau, motor._tau_crit(), delta_tau)
        cmd = motor.step(tau)
        log.append(
            {
                "tau": tau,
                "phase": cmd.phase.name,
                "causal_signal": causal.signal.name,
                "g_tt": causal.g_tt,
                "ds2": causal.tangent_ds2,
                "det_g": causal.det_g,
                "f_GHz": cmd.ring_frequency_hz / 1e9,
                "ballast": cmd.ballast_rate_kg_s,
                "rho": cmd.injection.rho,
                "emergency": cmd.emergency_rupture,
                "message": cmd.message,
            }
        )

    with LOG_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log[0].keys()))
        w.writeheader()
        w.writerows(log)

    print(f"Log saved: {LOG_CSV} ({len(log)} steps)")
    print("Phase summary:")
    phases_seen = []
    for row in log:
        if not phases_seen or phases_seen[-1] != row["phase"]:
            phases_seen.append(row["phase"])
    print("  ->", " -> ".join(phases_seen))
    return log


if __name__ == "__main__":
    simulate()
