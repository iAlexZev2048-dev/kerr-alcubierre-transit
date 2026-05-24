"""
Calibrates control thresholds from sweep_det_results.csv (or regenerates the sweep).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from engine_control import ranking_from_metric
from engine_metrics import InjectionSite, metrics_in_ship_chart, run_default_sweep
from metric_transition import blend_metric

ROOT = Path(__file__).resolve().parent
CSV_DEFAULT = ROOT / "sweep_det_results.csv"
CONFIG_DEFAULT = ROOT / "engine_config.json"


@dataclass
class CalibratedThresholds:
    MIN_DET_G: float
    Z_DIVERGENCE_LIMIT: float
    CRITICAL_HAWKING_LIMIT: float
    MIN_RANKING: float
    DEFAULT_Z_COMPENSATION: float = 0.85
    recommended_delta_tau: float = 2.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def load_csv_samples(path: Path) -> list[dict[str, float]]:
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


def calibrate_from_rows(rows: list[dict[str, float]]) -> CalibratedThresholds:
    dets = [abs(r["det_g_eff"]) for r in rows]
    psis = [r["psi"] for r in rows if r["psi"] > 0]

    det_min = min(dets) * 0.1
    det_min = max(det_min, 1e-12)

    ranking_vals = []
    site = InjectionSite()
    g_k, g_a = metrics_in_ship_chart(site)

    for r in rows[:20]:
        g = blend_metric(g_k, g_a, r["tau"], 0.0, r["delta_tau"])
        ranking_vals.append(ranking_from_metric(g))

    rank_min = min(ranking_vals) * 0.85 if ranking_vals else 0.5
    rank_min = max(0.1, min(rank_min, 3.5))

    hawking = 5e-4 if psis else 1e-3

    return CalibratedThresholds(
        MIN_DET_G=det_min,
        Z_DIVERGENCE_LIMIT=1e6,
        CRITICAL_HAWKING_LIMIT=hawking,
        MIN_RANKING=rank_min,
        recommended_delta_tau=2.0,
    )


def save_config(thresholds: CalibratedThresholds, path: Path = CONFIG_DEFAULT) -> None:
    path.write_text(json.dumps(thresholds.to_dict(), indent=2), encoding="utf-8")


def load_config(path: Path = CONFIG_DEFAULT) -> CalibratedThresholds | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return CalibratedThresholds(**data)


def apply_to_control(thresholds: CalibratedThresholds) -> None:
    import engine_control as ec

    ec.MIN_DET_G = thresholds.MIN_DET_G
    ec.CRITICAL_HAWKING_LIMIT = thresholds.CRITICAL_HAWKING_LIMIT
    ec.Z_DIVERGENCE_LIMIT = thresholds.Z_DIVERGENCE_LIMIT
    ec.MIN_RANKING = thresholds.MIN_RANKING
    ec.DEFAULT_Z_COMPENSATION = thresholds.DEFAULT_Z_COMPENSATION


def run_calibration(regenerate: bool = False) -> CalibratedThresholds:
    if regenerate or not CSV_DEFAULT.is_file():
        run_default_sweep(CSV_DEFAULT)
    rows = load_csv_samples(CSV_DEFAULT)
    thresholds = calibrate_from_rows(rows)
    save_config(thresholds)
    apply_to_control(thresholds)
    return thresholds


if __name__ == "__main__":
    t = run_calibration()
    print("Thresholds saved to", CONFIG_DEFAULT)
    print(json.dumps(t.to_dict(), indent=2))
