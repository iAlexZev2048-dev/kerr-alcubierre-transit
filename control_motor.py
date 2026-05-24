"""
Fase 3 — Lazo PID adaptativo para estabilización de métrica efectiva.
Traduce ψ(z) y T_target en comandos de inyección exótica, anillos ópticos y lastre.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from metricas_motor import InjectionSite, g_effective_at_tau
from transicion_metrica import (
    det_4x4,
    dpsi_dtau,
    psi,
    z_phase,
)

# --- constantes operativas ----------------------------------------------------

LIMITE_CRITICO_HAWKING = 1.0e-3
LIMITE_DIVERGENCIA_Z = 1.0e6
DET_G_MINIMO = 1.0e-12
Z_COMPENSATION_DEFAULT = 0.85
RANKING_MINIMO = 3.5


@dataclass
class Tensor:
    """Proxy de T_μν (componentes principales + acoplamiento de arrastre)."""

    rho: float = 0.0
    T_xx: float = 0.0
    T_yy: float = 0.0
    T_zz: float = 0.0
    T_tx: float = 0.0

    def __add__(self, other: Tensor) -> Tensor:
        return Tensor(
            self.rho + other.rho,
            self.T_xx + other.T_xx,
            self.T_yy + other.T_yy,
            self.T_zz + other.T_zz,
            self.T_tx + other.T_tx,
        )

    def __sub__(self, other: Tensor) -> Tensor:
        return Tensor(
            self.rho - other.rho,
            self.T_xx - other.T_xx,
            self.T_yy - other.T_yy,
            self.T_zz - other.T_zz,
            self.T_tx - other.T_tx,
        )

    def scale(self, s: float) -> Tensor:
        return Tensor(
            s * self.rho,
            s * self.T_xx,
            s * self.T_yy,
            s * self.T_zz,
            s * self.T_tx,
        )


def blend_tensor(psi_val: float, t_kerr: Tensor, t_alc: Tensor) -> Tensor:
    w = psi_val
    return t_kerr.scale(w) + t_alc.scale(1.0 - w)


def T_kerr_nominal() -> Tensor:
    return Tensor(rho=1.2e4, T_xx=4e3, T_yy=4e3, T_zz=8e3, T_tx=-1.5e3)


def T_alcubierre_nominal() -> Tensor:
    return Tensor(rho=-5e4, T_xx=-2e4, T_yy=-2e4, T_zz=-3e4, T_tx=0.0)


@dataclass
class SensoresNave:
    fluctuacion_vacio: float = 0.0
    curvatura_scalar: float = 0.0
    det_g_eff: float = 1.0
    T_zz_medido: float = 0.0
    ranking_jacobiano: float = 4.0


@dataclass
class GanhosPID:
    Kp: float = 2.0
    Ki: float = 0.4
    Kd: float = 0.15


class PIDAdaptativo:
    def __init__(self, ganhos: GanhosPID | None = None) -> None:
        self._g = ganhos or GanhosPID()
        self._integral = 0.0
        self._error_prev = 0.0
        self.Kp_eff = self._g.Kp
        self.Ki_eff = self._g.Ki
        self.Kd_eff = self._g.Kd

    def actualizar_ganhos(self, dpsi_dtau: float, radiation_leak: float) -> None:
        escala_rampa = 1.0 + min(4.0, abs(dpsi_dtau) * 8.0)
        atenuacion = 1.0 / (1.0 + 50.0 * radiation_leak)
        self.Kp_eff = self._g.Kp * escala_rampa * atenuacion
        self.Ki_eff = self._g.Ki * escala_rampa * atenuacion
        self.Kd_eff = self._g.Kd * escala_rampa

    def paso(self, error: float, dt: float) -> float:
        if dt <= 0:
            return 0.0
        self._integral += error * dt
        deriv = (error - self._error_prev) / dt
        self._error_prev = error
        return self.Kp_eff * error + self.Ki_eff * self._integral + self.Kd_eff * deriv

    def reiniciar(self) -> None:
        self._integral = 0.0
        self._error_prev = 0.0


@dataclass
class ParametrosTransicion:
    tau_crit: float = 0.0
    delta_tau: float = 2.0
    z_shape: float = 1.0
    dt_control: float = 1.0e-4


@dataclass
class SalidaControl:
    inyeccion_aplicada: Tensor = field(default_factory=Tensor)
    frecuencia_anillos_hz: float = 0.0
    tasa_lastre_kg_s: float = 0.0
    ruptura_emergencia: bool = False
    modo_compensacion_z: bool = False


def error_tensor(target: Tensor, medido: Tensor) -> float:
    e_rho = target.rho - medido.rho
    e_zz = target.T_zz - medido.T_zz
    return math.hypot(e_rho, e_zz)


def frecuencia_anillos_desde_psi(psi_val: float, f_base_hz: float = 1e9) -> float:
    p = max(0.0, min(1.0, psi_val))
    return f_base_hz * (0.05 + 0.95 * p)


def tasa_lastre_desde_dpsi(dpsi_dtau: float, ganancia: float = 1e2) -> float:
    return ganancia * abs(dpsi_dtau)


def ajustar_eje_ortogonal(z_shape: float, factor: float = Z_COMPENSATION_DEFAULT) -> float:
    return z_shape * factor


def mapa_estable(s: SensoresNave) -> bool:
    return (
        abs(s.det_g_eff) > DET_G_MINIMO
        and s.ranking_jacobiano >= RANKING_MINIMO
        and abs(s.T_zz_medido) < LIMITE_DIVERGENCIA_Z
    )


def divergencia_eje_Z(s: SensoresNave) -> bool:
    return abs(s.T_zz_medido) >= LIMITE_DIVERGENCIA_Z or abs(s.det_g_eff) < DET_G_MINIMO


def ranking_desde_metrica(g_eff: list[list[float]]) -> float:
    """
    Proxy del rango de F_*: 4·|det(g_eff)|^(1/4) / tr(|g|).
    Cae si el mapa pierde volumen (espaguetización / chart degenerado).
    """
    det = abs(det_4x4(g_eff))
    tr = sum(abs(g_eff[i][j]) for i in range(4) for j in range(4))
    if tr < 1e-30:
        return 0.0
    return 4.0 * (det ** 0.25) / tr


def sensores_desde_metrica(
    site: InjectionSite,
    tau: float,
    par: ParametrosTransicion,
    *,
    fluctuacion_vacio: float = 0.0,
    T_zz_medido: float = 0.0,
) -> SensoresNave:
    g_eff = g_effective_at_tau(site, tau, par.tau_crit, par.delta_tau)
    return SensoresNave(
        fluctuacion_vacio=fluctuacion_vacio,
        det_g_eff=det_4x4(g_eff),
        T_zz_medido=T_zz_medido,
        ranking_jacobiano=ranking_desde_metrica(g_eff),
    )


def control_transicion_metrica(
    z_pos: float,
    t_actual: float,
    sensores: SensoresNave,
    T_medido: Tensor,
    pid: PIDAdaptativo,
    par: ParametrosTransicion,
    T_kerr: Tensor | None = None,
    T_alc: Tensor | None = None,
) -> SalidaControl:
    """
    Núcleo Fase 3 — equivalente al pseudocódigo C++ del documento de patente.
    """
    out = SalidaControl()
    t_k = T_kerr if T_kerr is not None else T_kerr_nominal()
    t_a = T_alc if T_alc is not None else T_alcubierre_nominal()
    z_shape = par.z_shape

    psi_val = psi(z_pos)
    dpsi = dpsi_dtau(t_actual, par.tau_crit, par.delta_tau)

    T_target = blend_tensor(psi_val, t_k, t_a)
    T_target.T_zz *= z_shape

    out.frecuencia_anillos_hz = frecuencia_anillos_desde_psi(psi_val)
    out.tasa_lastre_kg_s = tasa_lastre_desde_dpsi(dpsi)

    if divergencia_eje_Z(sensores) or not mapa_estable(sensores):
        out.ruptura_emergencia = True
        T_target = t_a
        z_shape = Z_COMPENSATION_DEFAULT

    radiation_leak = sensores.fluctuacion_vacio
    pid.actualizar_ganhos(dpsi, radiation_leak)

    inyeccion = T_target

    if radiation_leak > LIMITE_CRITICO_HAWKING:
        out.modo_compensacion_z = True
        z_shape = ajustar_eje_ortogonal(z_shape)
        T_target.T_zz *= z_shape
        compensacion = Tensor(
            rho=radiation_leak * 1e5,
            T_zz=radiation_leak * 5e4,
        )
        inyeccion = T_target - compensacion

    err = error_tensor(inyeccion, T_medido)
    u_pid = pid.paso(err, par.dt_control)
    inyeccion.rho -= u_pid

    out.inyeccion_aplicada = inyeccion
    return out


def simular_fase3(
    n_pasos: int = 41,
    site: InjectionSite | None = None,
) -> list[dict[str, float | bool | str]]:
    site = site or InjectionSite()
    par = ParametrosTransicion()
    pid = PIDAdaptativo()
    T_medido = T_kerr_nominal()
    log: list[dict[str, float | bool | str]] = []

    for i in range(n_pasos):
        tau = par.tau_crit + (i / (n_pasos - 1) - 0.5) * par.delta_tau if n_pasos > 1 else par.tau_crit
        z = z_phase(tau, par.tau_crit, par.delta_tau)
        hawking = 1.5e-3 if abs(z) < 0.05 else 2e-4
        sensores = sensores_desde_metrica(
            site, tau, par, fluctuacion_vacio=hawking, T_zz_medido=T_medido.T_zz
        )
        out = control_transicion_metrica(z, tau, sensores, T_medido, pid, par)
        T_medido.rho += 0.3 * (out.inyeccion_aplicada.rho - T_medido.rho)
        log.append(
            {
                "tau": tau,
                "z": z,
                "psi": psi(z),
                "det_g_eff": sensores.det_g_eff,
                "ranking": sensores.ranking_jacobiano,
                "f_GHz": out.frecuencia_anillos_hz / 1e9,
                "lastre_kg_s": out.tasa_lastre_kg_s,
                "rho_cmd": out.inyeccion_aplicada.rho,
                "emergencia": out.ruptura_emergencia,
                "comp_Z": out.modo_compensacion_z,
            }
        )
    return log


def imprimir_simulacion(log: list[dict[str, float | bool | str]]) -> None:
    print("=== Fase 3 — PID adaptativo + ψ(z) ===")
    print("tau      z      psi    det(g)   rank   f_GHz  lastre  rho_cmd  emerg")
    for row in log:
        em = "SI" if row["emergencia"] else "no"
        print(
            f"{row['tau']:6.3f} {row['z']:6.3f} {row['psi']:6.4f} "
            f"{row['det_g_eff']:9.2e} {row['ranking']:5.3f} "
            f"{row['f_GHz']:6.3f} {row['lastre_kg_s']:7.2f} "
            f"{row['rho_cmd']:9.1f} {em}"
        )


if __name__ == "__main__":
    imprimir_simulacion(simular_fase3())
