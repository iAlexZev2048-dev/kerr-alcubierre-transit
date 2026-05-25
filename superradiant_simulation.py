"""
Speculative extension simulation: Superradiant Laser Harvester & Shield Deflection.
Models energy extraction from the Kerr black hole to offset Alcubierre warp bubble costs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine_metrics import InjectionSite, kerr_outer_horizon
from metric_transition import dpsi_dtau, psi_prime, z_phase
from energy_budget import penrose_efficiency, alcubierre_bubble_energy


@dataclass
class SuperradiantStats:
    tau: float
    psi_val: float
    energy_needed_raw: float
    shield_thermal_load: float
    energy_harvested: float
    net_energy_balance: float
    stable: bool
    secondary_bus_energy: float
    power_source: str
    handover_state: str


class SuperradiantEngine:
    def __init__(
        self,
        site: InjectionSite | None = None,
        shield_efficiency: float = 0.95,
        laser_base_power: float = 1.0e-5,  # positive laser seed in G=c=1
        superradiant_gain_rate: float = 1.5,  # exponential amplification factor in ergosphere
    ) -> None:
        self.site = site or InjectionSite()
        self.shield_efficiency = shield_efficiency
        self.laser_base_power = laser_base_power
        self.superradiant_gain_rate = superradiant_gain_rate
        
        # Dual Bus System
        self.secondary_bus_energy = 1.0e-2  # Quantum capacitor bank initial charge
        self.secondary_bus_capacity = 1.5e-2  # Max capacitor capacity

    def simulate_step(self, tau: float, tau_crit: float, delta_tau: float) -> SuperradiantStats:
        z = z_phase(tau, tau_crit, delta_tau)
        w = 1.0 - z**2
        psi_val = math.exp(-1.0 / w) if abs(z) < 1.0 else 0.0

        # 1. Alcubierre bubble requirements
        e_alc = alcubierre_bubble_energy(self.site.vs, self.site.bubble_radius, self.site.sigma)
        
        # Peak energy demand scales with dpsi/dtau
        dpsi = dpsi_dtau(tau, tau_crit, delta_tau)
        energy_needed_raw = e_alc * abs(dpsi)

        # 2. Deflection shield efficiency: redirects 95% of the thermal load
        shield_thermal_load = energy_needed_raw * (1.0 - self.shield_efficiency)

        # 3. Dual-Bus Power Routing & Handover
        if tau < -0.48:
            # ESTADO_PRE_TRANSITO
            handover_state = "PRE_TRAN"
            power_source = "SEC"
            energy_harvested = 0.0
            # Powered 100% by Secondary Bus (Capacitors)
            self.secondary_bus_energy = max(0.0, self.secondary_bus_energy - shield_thermal_load)
            net_energy_balance = -shield_thermal_load
        elif -0.48 <= tau < 0.72:
            # ESTADO_HANDOVER_POSITIVO or COHERENT_TRANSIT
            if tau <= 0.00:
                handover_state = "HAND_POS"
            else:
                handover_state = "COHERENT"
            power_source = "PRI"
            
            # Superradiant laser harvesting active in the ergosphere
            if psi_val > 0.0:
                amplification = math.exp(self.superradiant_gain_rate * (tau + delta_tau))
                energy_harvested = self.laser_base_power * amplification * psi_val
            else:
                energy_harvested = 0.0
            
            net_energy_balance = energy_harvested - shield_thermal_load
            # Route excess harvested energy to recharge the Secondary Bus
            if net_energy_balance > 0.0:
                self.secondary_bus_energy = min(
                    self.secondary_bus_capacity,
                    self.secondary_bus_energy + net_energy_balance
                )
        else:
            # ESTADO_HANDOVER_NEGATIVO (Predictive Cutoff at tau >= 0.72)
            handover_state = "HAND_NEG"
            power_source = "SEC"
            energy_harvested = 0.0
            # Powered 100% by Secondary Bus
            self.secondary_bus_energy = max(0.0, self.secondary_bus_energy - shield_thermal_load)
            net_energy_balance = -shield_thermal_load

        # The system is stable if the secondary bus has charge or if the net balance is positive
        if power_source == "SEC":
            stable = self.secondary_bus_energy > 0.0
        else:
            stable = (net_energy_balance >= 0.0) or (self.secondary_bus_energy > 0.0)

        return SuperradiantStats(
            tau=tau,
            psi_val=psi_val,
            energy_needed_raw=energy_needed_raw,
            shield_thermal_load=shield_thermal_load,
            energy_harvested=energy_harvested,
            net_energy_balance=net_energy_balance,
            stable=stable,
            secondary_bus_energy=self.secondary_bus_energy,
            power_source=power_source,
            handover_state=handover_state,
        )


def run_superradiant_sweep(n_steps: int = 21, delta_tau: float = 2.0) -> None:
    engine = SuperradiantEngine(
        shield_efficiency=0.95,        # 95% deflection
        laser_base_power=2.0e-4,       # Seed laser
        superradiant_gain_rate=1.8,    # Amplification multiplier
    )
    
    tau_crit = 0.0
    half = delta_tau * 1.2
    step = (2.0 * half) / (n_steps - 1)
    tau_grid = [tau_crit - half + i * step for i in range(n_steps)]

    print("=== Speculative Superradiant Harvester & Shield Simulation ===")
    print(f"Shield Efficiency: {engine.shield_efficiency * 100:.1f}%")
    print(f"Laser Seed Power:  {engine.laser_base_power:.2e}")
    print(f"Superradiant Gain: {engine.superradiant_gain_rate:.2f}\n")
    
    print("tau      psi    Needed(Raw)   Shield_Load   Harvested     Net_Balance   Cap_Charge  Bus  State     Stable?")
    print("-" * 110)

    for tau in tau_grid:
        stats = engine.simulate_step(tau, tau_crit, delta_tau)
        status = "YES" if stats.stable else "NO (FAIL)"
        print(
            f"{stats.tau:6.3f} {stats.psi_val:6.4f}  "
            f"{stats.energy_needed_raw:12.3e}  {stats.shield_thermal_load:12.3e}  "
            f"{stats.energy_harvested:12.3e}  {stats.net_energy_balance:12.3e}  "
            f"{stats.secondary_bus_energy:11.3e}  {stats.power_source:3s}  {stats.handover_state:8s}  {status}"
        )


if __name__ == "__main__":
    run_superradiant_sweep()
