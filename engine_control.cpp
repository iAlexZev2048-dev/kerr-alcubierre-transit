/**
 * Phase 3 loop demonstration — compile with:
 *   g++ -std=c++17 -O2 -o control_demo engine_control.cpp
 */

#include "engine_control.hpp"
#include <cstdio>

int main() {
    using namespace motor;

    AdaptivePid pid;
    TransitionParameters par;
    par.delta_tau = 2.0;
    par.tau_crit = 0.0;
    par.dt_control = 0.01;

    ShipSensors sensors{};
    Tensor T_measured = T_kerr_nominal();

    printf("=== Phase 3 Simulation: control_metric_transition ===\n");
    printf("tau\tz\tpsi\tring_freq_GHz\tballast_kg/s\temergency\n");

    for (int i = -20; i <= 20; ++i) {
        const double tau = par.tau_crit + (i / 20.0) * par.delta_tau;
        const double z = z_from_tau(tau, par.tau_crit, par.delta_tau);

        sensors.det_g_eff = 1.0 - 0.3 * (1.0 - calculate_bump_function(z));
        sensors.vacuum_fluctuation = (i == 0) ? 1.5e-3 : 2.0e-4;
        sensors.measured_T_zz = T_measured.T_zz;
        sensors.jacobian_ranking = 4.0;

        auto out = control_metric_transition(
            z, tau, sensors, T_measured, pid, par);

        T_measured.rho += 0.3 * (out.applied_injection.rho - T_measured.rho);

        printf("%.3f\t%.3f\t%.4f\t%.3f\t%.2f\t%s\n",
               tau, z, calculate_bump_function(z),
               out.ring_frequency_hz / 1.0e9,
               out.ballast_rate_kg_s,
               out.emergency_rupture ? "YES" : "no");
    }

    return 0;
}
