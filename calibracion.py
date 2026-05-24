"""
Calibra umbrales de control desde sweep_det_results.csv (o regenera el barrido).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from control_motor import ranking_desde_metrica
from metricas_motor import InjectionSite, metrics_in_ship_chart, run_default_sweep
from transicion_metrica import blend_metric

ROOT = Path(__file__).resolve().parent
CSV_DEFAULT = ROOT / "sweep_det_results.csv"
CONFIG_DEFAULT = ROOT / "motor_config.json"


@dataclass
class UmbralesCalibrados:
    DET_G_MINIMO: float
    LIMITE_DIVERGENCIA_Z: float
    LIMITE_CRITICO_HAWKING: float
    RANKING_MINIMO: float
    Z_COMPENSATION_DEFAULT: float = 0.85
    delta_tau_recomendado: float = 2.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def cargar_muestras_csv(path: Path) -> list[dict[str, float]]:
    import csv

    rows: list[dict[str, float]] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "tau": float(row["tau"]),
                    "delta_tau": float(row["delta_tau"]),
                    "psi": float(row["psi"]),
                    "det_g_eff": float(row["det_g_eff"]),
                }
            )
    return rows


def calibrar_desde_filas(rows: list[dict[str, float]]) -> UmbralesCalibrados:
    dets = [abs(r["det_g_eff"]) for r in rows]
    psis = [r["psi"] for r in rows if r["psi"] > 0]

    det_min = min(dets) * 0.1
    det_min = max(det_min, 1e-12)

    ranking_vals = []
    site = InjectionSite()
    g_k, g_a = metrics_in_ship_chart(site)

    for r in rows[:20]:
        g = blend_metric(g_k, g_a, r["tau"], 0.0, r["delta_tau"])
        ranking_vals.append(ranking_desde_metrica(g))

    rank_min = min(ranking_vals) * 0.85 if ranking_vals else 0.5
    rank_min = max(0.1, min(rank_min, 3.5))

    hawking = 5e-4 if psis else 1e-3

    return UmbralesCalibrados(
        DET_G_MINIMO=det_min,
        LIMITE_DIVERGENCIA_Z=1e6,
        LIMITE_CRITICO_HAWKING=hawking,
        RANKING_MINIMO=rank_min,
        delta_tau_recomendado=2.0,
    )


def guardar_config(umbrales: UmbralesCalibrados, path: Path = CONFIG_DEFAULT) -> None:
    path.write_text(json.dumps(umbrales.to_dict(), indent=2), encoding="utf-8")


def cargar_config(path: Path = CONFIG_DEFAULT) -> UmbralesCalibrados | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return UmbralesCalibrados(**data)


def aplicar_a_control(umbrales: UmbralesCalibrados) -> None:
    import control_motor as cm

    cm.DET_G_MINIMO = umbrales.DET_G_MINIMO
    cm.LIMITE_CRITICO_HAWKING = umbrales.LIMITE_CRITICO_HAWKING
    cm.LIMITE_DIVERGENCIA_Z = umbrales.LIMITE_DIVERGENCIA_Z
    cm.RANKING_MINIMO = umbrales.RANKING_MINIMO
    cm.Z_COMPENSATION_DEFAULT = umbrales.Z_COMPENSATION_DEFAULT


def ejecutar_calibracion(regenerar: bool = False) -> UmbralesCalibrados:
    if regenerar or not CSV_DEFAULT.is_file():
        run_default_sweep(CSV_DEFAULT)
    rows = cargar_muestras_csv(CSV_DEFAULT)
    umbrales = calibrar_desde_filas(rows)
    guardar_config(umbrales)
    aplicar_a_control(umbrales)
    return umbrales


if __name__ == "__main__":
    u = ejecutar_calibracion()
    print("Umbrales guardados en", CONFIG_DEFAULT)
    print(json.dumps(u.to_dict(), indent=2))
