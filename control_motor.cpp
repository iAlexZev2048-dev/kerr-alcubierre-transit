/**
 * Demostración del lazo Fase 3 — compilar:
 *   g++ -std=c++17 -O2 -o control_demo control_motor.cpp
 */

#include "control_motor.hpp"
#include <cstdio>

int main() {
    using namespace motor;

    PIDAdaptativo pid;
    ParametrosTransicion par;
    par.delta_tau = 2.0;
    par.tau_crit = 0.0;
    par.dt_control = 0.01;

    SensoresNave sensores{};
    Tensor T_medido = T_kerr_nominal();

    printf("=== Simulacion Fase 3: control_transicion_metrica ===\n");
    printf("tau\tz\tpsi\tf_anillos_GHz\tlastre_kg/s\temergencia\n");

    for (int i = -20; i <= 20; ++i) {
        const double tau = par.tau_crit + (i / 20.0) * par.delta_tau;
        const double z = z_desde_tau(tau, par.tau_crit, par.delta_tau);

        sensores.det_g_eff = 1.0 - 0.3 * (1.0 - calcular_funcion_bump(z));
        sensores.fluctuacion_vacio = (i == 0) ? 1.5e-3 : 2.0e-4;
        sensores.T_zz_medido = T_medido.T_zz;
        sensores.ranking_jacobiano = 4.0;

        auto out = control_transicion_metrica(
            z, tau, sensores, T_medido, pid, par);

        T_medido.rho += 0.3 * (out.inyeccion_aplicada.rho - T_medido.rho);

        printf("%.3f\t%.3f\t%.4f\t%.3f\t%.2f\t%s\n",
               tau, z, calcular_funcion_bump(z),
               out.frecuencia_anillos_hz / 1.0e9,
               out.tasa_lastre_kg_s,
               out.ruptura_emergencia ? "SI" : "no");
    }

    return 0;
}
