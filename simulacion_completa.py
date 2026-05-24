"""
Simulación encadenada Fase 0 → 3 con telemetría CSV y calibración previa.
"""

from __future__ import annotations

import csv
from pathlib import Path

from calibracion import cargar_config, ejecutar_calibracion
from fases_motor import ConfigMotor, Fase, MotorCausal, TelemetriaNaveA
from metricas_motor import InjectionSite, default_tau_grid
from presupuesto_energia import evaluar_presupuesto, tabla_presupuesto_texto
from tau_crit import evaluar_estado_causal

ROOT = Path(__file__).resolve().parent
LOG_CSV = ROOT / "simulacion_completa.csv"


def simular(
    n_tau: int = 61,
    delta_tau: float = 2.0,
    calibrar: bool = True,
) -> list[dict]:
    if calibrar:
        ejecutar_calibracion(regenerar=False)
    elif cargar_config():
        from calibracion import aplicar_a_control, cargar_config

        u = cargar_config()
        if u:
            aplicar_a_control(u)

    site = InjectionSite()
    cfg = ConfigMotor(site=site)
    cfg.par.delta_tau = delta_tau
    motor = MotorCausal(cfg)
    motor.set_beacon(TelemetriaNaveA(reloj_beacon=1.0, enlace_activo=True))

    tau_grid = default_tau_grid(0.0, delta_tau * 1.5, n_tau)
    cfg.par.dt_control = tau_grid[1] - tau_grid[0]
    motor.calibrar_tau_crit(tau_grid)

    pb = evaluar_presupuesto(site, motor._tau_crit(), delta_tau)
    print(tabla_presupuesto_texto(pb))
    print(f"\ntau_crit calibrado = {motor._tau_crit():.6f}\n")

    log: list[dict] = []
    for tau in tau_grid:
        causal = evaluar_estado_causal(site, tau, motor._tau_crit(), delta_tau)
        cmd = motor.paso(tau)
        log.append(
            {
                "tau": tau,
                "fase": cmd.fase.name,
                "senal_causal": causal.senal.name,
                "g_tt": causal.g_tt,
                "ds2": causal.ds2_tangente,
                "det_g": causal.det_g,
                "f_GHz": cmd.frecuencia_anillos_hz / 1e9,
                "lastre": cmd.tasa_lastre_kg_s,
                "rho": cmd.inyeccion.rho,
                "emergencia": cmd.ruptura_emergencia,
                "msg": cmd.mensaje,
            }
        )

    with LOG_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log[0].keys()))
        w.writeheader()
        w.writerows(log)

    print(f"Log guardado: {LOG_CSV} ({len(log)} pasos)")
    print("Resumen de fases:")
    fases_vistas = []
    for row in log:
        if not fases_vistas or fases_vistas[-1] != row["fase"]:
            fases_vistas.append(row["fase"])
    print("  ->", " -> ".join(fases_vistas))
    return log


if __name__ == "__main__":
    simular()
