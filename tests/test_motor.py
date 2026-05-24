"""Tests del motor causal (stdlib unittest)."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from transicion_metrica import psi, psi_prime, det_4x4, blend_metric, z_phase
from metricas_motor import InjectionSite, metrics_in_ship_chart, g_effective_at_tau
from einstein_proxy import T_from_g, condiciones_energia
from tau_crit import detectar_tau_crit, evaluar_estado_causal
from fases_motor import MotorCausal, Fase, ConfigMotor
from presupuesto_energia import evaluar_presupuesto


class TestBump(unittest.TestCase):
    def test_psi_en_borde(self):
        self.assertEqual(psi(1.0), 0.0)
        self.assertEqual(psi(-1.0), 0.0)

    def test_psi_centro(self):
        self.assertAlmostEqual(psi(0.0), math.exp(-1.0), places=12)

    def test_derivada_cero_fuera(self):
        self.assertEqual(psi_prime(2.0), 0.0)


class TestMetricas(unittest.TestCase):
    def test_det_kerr_no_cero(self):
        g_k, _ = metrics_in_ship_chart(InjectionSite())
        self.assertNotAlmostEqual(det_4x4(g_k), 0.0)

    def test_g_eff_finita_en_rampa(self):
        site = InjectionSite()
        for z in [-0.9, 0.0, 0.9]:
            tau = z * 0.5  # tau_crit=0, delta_tau=1
            g = g_effective_at_tau(site, tau, 0.0, 1.0)
            self.assertTrue(math.isfinite(det_4x4(g)))


class TestTauCrit(unittest.TestCase):
    def test_detectar_devuelve_float(self):
        site = InjectionSite()
        grid = [i * 0.1 - 1.0 for i in range(21)]
        tc = detectar_tau_crit(site, grid, 2.0, 0.0)
        self.assertIsInstance(tc, float)


class TestFases(unittest.TestCase):
    def test_avanza_desde_calibracion(self):
        m = MotorCausal(ConfigMotor())
        m.fase = Fase.CALIBRACION
        cmd = m.paso(tau=0.0)
        self.assertIn(cmd.fase, (Fase.CALIBRACION, Fase.DESCENSO, Fase.ABORT))


class TestPresupuesto(unittest.TestCase):
    def test_presupuesto_campos(self):
        pb = evaluar_presupuesto()
        self.assertGreater(pb.eta_penrose, 0.0)
        self.assertGreater(pb.E_penrose_max, 0.0)


class TestEinsteinProxy(unittest.TestCase):
    def test_T_desde_minkowski_cercano_cero(self):
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
