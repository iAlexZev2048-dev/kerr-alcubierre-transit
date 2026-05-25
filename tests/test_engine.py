"""Causal engine unit tests (stdlib unittest)."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from metric_transition import psi, psi_prime, det_4x4, blend_metric, z_phase
from engine_metrics import InjectionSite, metrics_in_local_chart, g_effective_at_tau
from einstein_proxy import T_from_g, energy_conditions
from tau_crit import detect_tau_crit, evaluate_causal_state
from engine_phases import TransitionSimulation, Phase, EngineConfig
from energy_budget import evaluate_budget


class TestBump(unittest.TestCase):
    def test_psi_at_boundary(self):
        self.assertEqual(psi(1.0), 0.0)
        self.assertEqual(psi(-1.0), 0.0)

    def test_psi_center(self):
        self.assertAlmostEqual(psi(0.0), math.exp(-1.0), places=12)

    def test_derivative_zero_outside(self):
        self.assertEqual(psi_prime(2.0), 0.0)


class TestMetrics(unittest.TestCase):
    def test_det_kerr_nonzero(self):
        g_k, _ = metrics_in_local_chart(InjectionSite())
        self.assertNotAlmostEqual(det_4x4(g_k), 0.0)

    def test_g_eff_finite_in_ramp(self):
        site = InjectionSite()
        for z in [-0.9, 0.0, 0.9]:
            tau = z * 0.5  # tau_crit=0, delta_tau=1
            g = g_effective_at_tau(site, tau, 0.0, 1.0)
            self.assertTrue(math.isfinite(det_4x4(g)))


class TestTauCrit(unittest.TestCase):
    def test_detect_returns_float(self):
        site = InjectionSite()
        grid = [i * 0.1 - 1.0 for i in range(21)]
        tc = detect_tau_crit(site, grid, 2.0, 0.0)
        self.assertIsInstance(tc, float)


class TestPhases(unittest.TestCase):
    def test_advances_from_calibration(self):
        m = TransitionSimulation(EngineConfig())
        m.phase = Phase.CALIBRATION
        cmd = m.step(tau=0.0)
        self.assertIn(cmd.phase, (Phase.CALIBRATION, Phase.DESCENT, Phase.ABORT))


class TestBudget(unittest.TestCase):
    def test_budget_fields(self):
        pb = evaluate_budget()
        self.assertGreater(pb.penrose_efficiency, 0.0)
        self.assertGreater(pb.max_penrose_energy, 0.0)


class TestEinsteinProxy(unittest.TestCase):
    def test_T_from_minkowski_near_zero(self):
        eta = [
            [-1.0, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
        t = T_from_g(eta)
        self.assertAlmostEqual(t.rho, 0.0, places=10)


if __name__ == "__main__":
    unittest.main()
