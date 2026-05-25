/**
 * Phase 3 — Effective metric stabilization (Co-moving Frame).
 * Adaptive PID loop + Kerr → Alcubierre handover via ψ(z).
 * Arbitrary units; link real sensors in flight implementation.
 */

#pragma once

#include <array>
#include <cmath>
#include <algorithm>

namespace motor {

constexpr double CRITICAL_HAWKING_LIMIT = 1.0e-3;
constexpr double Z_DIVERGENCE_LIMIT     = 1.0e6;
constexpr double MIN_DET_G               = 1.0e-12;
constexpr double DEFAULT_Z_COMPENSATION  = 0.85;

// Reduced stress-energy tensor (principal components + Z-coupling)
struct Tensor {
    double rho{0.0};      // energy density (rho < 0 -> exotic)
    double T_xx{0.0};
    double T_yy{0.0};
    double T_zz{0.0};      // critical orthogonal axis (spaghettification)
    double T_tx{0.0};      // frame-dragging (Kerr)
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
inline double calculate_bump_function(double z_pos) {
    if (std::abs(z_pos) >= 1.0) return 0.0;
    const double u = 1.0 - z_pos * z_pos;
    return std::exp(-1.0 / u);
}

inline double bump_derivative_z(double z_pos) {
    if (std::abs(z_pos) >= 1.0) return 0.0;
    const double u = 1.0 - z_pos * z_pos;
    return -2.0 * z_pos * std::exp(-1.0 / u) / (u * u);
}

inline double z_from_tau(double tau, double tau_crit, double delta_tau) {
    return 2.0 * (tau - tau_crit) / delta_tau;
}

struct TelemetrySensors {
    double vacuum_fluctuation{0.0};   // Hawking proxy
    double scalar_curvature{0.0};    // |R| or proxy
    double det_g_eff{1.0};
    double measured_T_zz{0.0};
    double jacobian_ranking{4.0};   // effective range of the F_* map (4 = stable)
};

struct PidGains {
    double Kp{2.0};
    double Ki{0.4};
    double Kd{0.15};
};

class AdaptivePid {
public:
    explicit AdaptivePid(PidGains g = {}) : gains_(g) {}

    // Modulates gains with |dψ/dτ| and radiation leak
    void update_gains(double dpsi_dtau, double radiation_leak) {
        const double ramp_scale = 1.0 + std::min(4.0, std::abs(dpsi_dtau) * 8.0);
        const double attenuation = 1.0 / (1.0 + 50.0 * radiation_leak);
        Kp_eff_ = gains_.Kp * ramp_scale * attenuation;
        Ki_eff_ = gains_.Ki * ramp_scale * attenuation;
        Kd_eff_ = gains_.Kd * ramp_scale;
    }

    // scalar error: norm of ρ and T_zz (critical axis)
    double step(double error, double dt) {
        if (dt <= 0.0) return 0.0;
        integral_ += error * dt;
        const double deriv = (error - error_prev_) / dt;
        error_prev_ = error;
        return Kp_eff_ * error + Ki_eff_ * integral_ + Kd_eff_ * deriv;
    }

    void reset() { integral_ = 0.0; error_prev_ = 0.0; }

private:
    PidGains gains_;
    double Kp_eff_{gains_.Kp}, Ki_eff_{gains_.Ki}, Kd_eff_{gains_.Kd};
    double integral_{0.0}, error_prev_{0.0};
};

struct ControlOutput {
    Tensor applied_injection{};
    double ring_frequency_hz{0.0};
    double ballast_rate_kg_s{0.0};
    bool emergency_rupture{false};
    bool z_compensation_mode{false};
};

// Nominal T profiles (calibrate with in-flight metric)
inline Tensor T_kerr_nominal() {
    return {1.2e4, 4.0e3, 4.0e3, 8.0e3, -1.5e3};  // ergosphere, frame-dragging in T_tx
}

inline Tensor T_alcubierre_nominal() {
    return {-5.0e4, -2.0e4, -2.0e4, -3.0e4, 0.0}; // exotic matter
}

inline double sensor_vacuum_fluctuations(const TelemetrySensors& s) {
    return s.vacuum_fluctuation;
}

inline double error_tensor(const Tensor& target, const Tensor& measured) {
    const double e_rho = target.rho - measured.rho;
    const double e_zz  = target.T_zz - measured.T_zz;
    return std::sqrt(e_rho * e_rho + e_zz * e_zz);
}

// Optical loop frequency ∝ ψ (gradual handover of light cone)
inline double ring_frequency_from_psi(double psi, double f_base_hz = 1.0e9) {
    const double p = std::clamp(psi, 0.0, 1.0);
    return f_base_hz * (0.05 + 0.95 * p);  // never turn off completely during transition
}

// Penrose ballast ∝ |dψ/dτ| (Phase 2 / angular handover)
inline double ballast_rate_from_dpsi(double dpsi_dtau, double gain = 1.0e2) {
    return gain * std::abs(dpsi_dtau);
}

// Topological stability: range of the differential F_* ≈ det ≠ 0 and bounded T_zz
inline bool is_map_stable(const TelemetrySensors& s) {
    return std::abs(s.det_g_eff) > MIN_DET_G
        && s.jacobian_ranking >= 3.5
        && std::abs(s.measured_T_zz) < Z_DIVERGENCE_LIMIT;
}

inline bool is_z_axis_diverging(const TelemetrySensors& s) {
    return std::abs(s.measured_T_zz) >= Z_DIVERGENCE_LIMIT
        || std::abs(s.det_g_eff) < MIN_DET_G;
}

struct TransitionParameters {
    double tau_crit{0.0};
    double delta_tau{2.0};
    double z_shape{1.0};           // Z-axis shape factor (1 = nominal)
    double dt_control{1.0e-4};     // PID loop step [s]
};

inline void adjust_orthogonal_axis(double& z_shape, double factor = DEFAULT_Z_COMPENSATION) {
    z_shape *= factor;
}

// --- Phase 3 Core (equivalent to the pseudocode) -----------------------------

inline ControlOutput control_metric_transition(
    double z_pos,
    double /*t_actual*/,
    const TelemetrySensors& sensors,
    const Tensor& T_measured,
    AdaptivePid& pid,
    TransitionParameters p,
    Tensor T_kerr = T_kerr_nominal(),
    Tensor T_alc = T_alcubierre_nominal()
) {
    ControlOutput out{};
    TransitionParameters par = p;

    // 1. Blending factor ψ(z)
    const double psi = calculate_bump_function(z_pos);
    const double dpsi_dtau = bump_derivative_z(z_pos) * (2.0 / par.delta_tau);

    // 2. Mixed T_μν target
    Tensor T_target = blend_tensor(psi, T_kerr, T_alc);
    // Compensate for Z shape factor (narrow if the chart deforms)
    T_target.T_zz *= par.z_shape;

    // Hardware handover / Phase 2
    out.ring_frequency_hz = ring_frequency_from_psi(psi);
    out.ballast_rate_kg_s = ballast_rate_from_dpsi(dpsi_dtau);

    // Protection: topological collapse -> pure Alcubierre shield
    if (is_z_axis_diverging(sensors) || !is_map_stable(sensors)) {
        out.emergency_rupture = true;
        T_target = T_alc;
        par.z_shape = DEFAULT_Z_COMPENSATION;
    }

    const double radiation_leak = sensor_vacuum_fluctuations(sensors);
    pid.update_gains(dpsi_dtau, radiation_leak);

    Tensor injection = T_target;

    if (radiation_leak > CRITICAL_HAWKING_LIMIT) {
        out.z_compensation_mode = true;
        adjust_orthogonal_axis(par.z_shape);
        T_target.T_zz *= par.z_shape;
        const Tensor compensation = {radiation_leak * 1.0e5, 0.0, 0.0, radiation_leak * 5.0e4, 0.0};
        injection = T_target - compensation;
    }

    // PID over exotic density (rho target vs measured)
    const double err = error_tensor(injection, T_measured);
    const double u_pid = pid.step(err, par.dt_control);
    injection.rho -= u_pid;  // injection correction

    out.applied_injection = injection;
    return out;
}

}  // namespace motor
