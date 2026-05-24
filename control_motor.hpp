/**
 * Fase 3 — Estabilización de métrica efectiva (Nave B).
 * Bucle PID adaptativo + handover Kerr → Alcubierre vía ψ(z).
 * Unidades arbitrarias; enlazar sensores reales en implementación de vuelo.
 */

#pragma once

#include <array>
#include <cmath>
#include <algorithm>

namespace motor {

constexpr double LIMITE_CRITICO_HAWKING = 1.0e-3;
constexpr double LIMITE_DIVERGENCIA_Z   = 1.0e6;
constexpr double DET_G_MINIMO           = 1.0e-12;
constexpr double Z_COMPENSATION_DEFAULT = 0.85;

// Tensor de energía-impulso reducido (componentes principales + acoplamiento Z)
struct Tensor {
    double rho{0.0};      // densidad de energía (ρ < 0 → exótica)
    double T_xx{0.0};
    double T_yy{0.0};
    double T_zz{0.0};      // eje ortogonal crítico (espaguetización)
    double T_tx{0.0};      // arrastre de marco (Kerr)
};

inline Tensor operator+(const Tensor& a, const Tensor& b) {
    return {a.rho + b.rho, a.T_xx + b.T_xx, a.T_yy + b.T_yy, a.T_zz + b.T_zz, a.T_tx + b.T_tx};
}

inline Tensor operator-(const Tensor& a, const Tensor& b) {
    return {a.rho - b.rho, a.T_xx - b.T_xx, a.T_yy - b.T_yy, a.T_zz - b.T_zz, a.T_tx - b.T_tx};
}

inline Tensor operator*(double s, const Tensor& t) {
    return {s * t.rho, s * t.T_xx, s * t.T_yy, s * t.T_zz, s * t.T_tx};
}

inline Tensor blend_tensor(double psi, const Tensor& T_kerr, const Tensor& T_alc) {
    return psi * T_kerr + (1.0 - psi) * T_alc;
}

// ψ(z) bump C^∞
inline double calcular_funcion_bump(double z_pos) {
    if (std::abs(z_pos) >= 1.0) return 0.0;
    const double u = 1.0 - z_pos * z_pos;
    return std::exp(-1.0 / u);
}

inline double derivada_bump_z(double z_pos) {
    if (std::abs(z_pos) >= 1.0) return 0.0;
    const double u = 1.0 - z_pos * z_pos;
    return -2.0 * z_pos * std::exp(-1.0 / u) / (u * u);
}

inline double z_desde_tau(double tau, double tau_crit, double delta_tau) {
    return 2.0 * (tau - tau_crit) / delta_tau;
}

struct SensoresNave {
    double fluctuacion_vacio{0.0};   // proxy Hawking
    double curvatura_scalar{0.0};    // |R| o proxy
    double det_g_eff{1.0};
    double T_zz_medido{0.0};
    double ranking_jacobiano{4.0};   // rango efectivo del mapa F_* (4 = estable)
};

struct GanhosPID {
    double Kp{2.0};
    double Ki{0.4};
    double Kd{0.15};
};

class PIDAdaptativo {
public:
    explicit PIDAdaptativo(GanhosPID g = {}) : ganhos_(g) {}

    // Modula ganancias con |dψ/dτ| y fuga de radiación
    void actualizar_ganhos(double dpsi_dtau, double radiation_leak) {
        const double escala_rampa = 1.0 + std::min(4.0, std::abs(dpsi_dtau) * 8.0);
        const double atenuacion = 1.0 / (1.0 + 50.0 * radiation_leak);
        Kp_eff_ = ganhos_.Kp * escala_rampa * atenuacion;
        Ki_eff_ = ganhos_.Ki * escala_rampa * atenuacion;
        Kd_eff_ = ganhos_.Kd * escala_rampa;
    }

    // error escalar: norma de ρ y T_zz (eje crítico)
    double paso(double error, double dt) {
        if (dt <= 0.0) return 0.0;
        integral_ += error * dt;
        const double deriv = (error - error_prev_) / dt;
        error_prev_ = error;
        return Kp_eff_ * error + Ki_eff_ * integral_ + Kd_eff_ * deriv;
    }

    void reiniciar() { integral_ = 0.0; error_prev_ = 0.0; }

private:
    GanhosPID ganhos_;
    double Kp_eff_{ganhos_.Kp}, Ki_eff_{ganhos_.Ki}, Kd_eff_{ganhos_.Kd};
    double integral_{0.0}, error_prev_{0.0};
};

struct SalidaControl {
    Tensor inyeccion_aplicada{};
    double frecuencia_anillos_hz{0.0};
    double tasa_lastre_kg_s{0.0};
    bool ruptura_emergencia{false};
    bool modo_compensacion_z{false};
};

// Perfiles nominales de T (calibrar con métrica en vuelo)
inline Tensor T_kerr_nominal() {
    return {1.2e4, 4.0e3, 4.0e3, 8.0e3, -1.5e3};  // ergósfera, arrastre en T_tx
}

inline Tensor T_alcubierre_nominal() {
    return {-5.0e4, -2.0e4, -2.0e4, -3.0e4, 0.0}; // materia exótica
}

inline double sensor_fluctuaciones_vacio(const SensoresNave& s) {
    return s.fluctuacion_vacio;
}

inline double error_tensor(const Tensor& target, const Tensor& medido) {
    const double e_rho = target.rho - medido.rho;
    const double e_zz  = target.T_zz - medido.T_zz;
    return std::sqrt(e_rho * e_rho + e_zz * e_zz);
}

// Frecuencia de bucle óptico ∝ ψ (handover gradual del cono de luz)
inline double frecuencia_anillos_desde_psi(double psi, double f_base_hz = 1.0e9) {
    const double p = std::clamp(psi, 0.0, 1.0);
    return f_base_hz * (0.05 + 0.95 * p);  // nunca apagar del todo en transición
}

// Lastre Penrose ∝ |dψ/dτ| (Fase 2 / handover angular)
inline double tasa_lastre_desde_dpsi(double dpsi_dtau, double ganancia = 1.0e2) {
    return ganancia * std::abs(dpsi_dtau);
}

// Estabilidad topológica: rango del diferencial F_* ≈ det ≠ 0 y T_zz acotado
inline bool mapa_estable(const SensoresNave& s) {
    return std::abs(s.det_g_eff) > DET_G_MINIMO
        && s.ranking_jacobiano >= 3.5
        && std::abs(s.T_zz_medido) < LIMITE_DIVERGENCIA_Z;
}

inline bool divergencia_eje_Z(const SensoresNave& s) {
    return std::abs(s.T_zz_medido) >= LIMITE_DIVERGENCIA_Z
        || std::abs(s.det_g_eff) < DET_G_MINIMO;
}

struct ParametrosTransicion {
    double tau_crit{0.0};
    double delta_tau{2.0};
    double z_shape{1.0};           // factor de forma eje Z (1 = nominal)
    double dt_control{1.0e-4};     // paso del lazo PID [s]
};

inline void ajustar_eje_ortogonal(double& z_shape, double factor = Z_COMPENSATION_DEFAULT) {
    z_shape *= factor;
}

// --- Núcleo Fase 3 (equivalente al pseudocódigo) -----------------------------

inline SalidaControl control_transicion_metrica(
    double z_pos,
    double /*t_actual*/,
    const SensoresNave& sensores,
    const Tensor& T_medido,
    PIDAdaptativo& pid,
    ParametrosTransicion p,
    Tensor T_kerr = T_kerr_nominal(),
    Tensor T_alc = T_alcubierre_nominal()
) {
    SalidaControl out{};
    ParametrosTransicion par = p;

    // 1. Factor de suavizado ψ(z)
    const double psi = calcular_funcion_bump(z_pos);
    const double dpsi_dtau = derivada_bump_z(z_pos) * (2.0 / par.delta_tau);

    // 2. Objetivo T_μν mezclado
    Tensor T_target = blend_tensor(psi, T_kerr, T_alc);
    // Compensar factor de forma en Z (estrechar si el chart se deforma)
    T_target.T_zz *= par.z_shape;

    // Handover hardware / Fase 2
    out.frecuencia_anillos_hz = frecuencia_anillos_desde_psi(psi);
    out.tasa_lastre_kg_s = tasa_lastre_desde_dpsi(dpsi_dtau);

    // Protección: colapso topológico → escudo Alcubierre puro
    if (divergencia_eje_Z(sensores) || !mapa_estable(sensores)) {
        out.ruptura_emergencia = true;
        T_target = T_alc;
        par.z_shape = Z_COMPENSATION_DEFAULT;
    }

    const double radiation_leak = sensor_fluctuaciones_vacio(sensores);
    pid.actualizar_ganhos(dpsi_dtau, radiation_leak);

    Tensor inyeccion = T_target;

    if (radiation_leak > LIMITE_CRITICO_HAWKING) {
        out.modo_compensacion_z = true;
        ajustar_eje_ortogonal(par.z_shape);
        T_target.T_zz *= par.z_shape;
        const Tensor compensacion = {radiation_leak * 1.0e5, 0.0, 0.0, radiation_leak * 5.0e4, 0.0};
        inyeccion = T_target - compensacion;
    }

    // PID sobre densidad exótica (ρ objetivo vs medido)
    const double err = error_tensor(inyeccion, T_medido);
    const double u_pid = pid.paso(err, par.dt_control);
    inyeccion.rho -= u_pid;  // corrección de inyección

    out.inyeccion_aplicada = inyeccion;
    return out;
}

}  // namespace motor
