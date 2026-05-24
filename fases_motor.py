"""
Máquina de estados Fase 0 → 3 para el motor causal (Nave A / Nave B).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from control_motor import (
    PIDAdaptativo,
    ParametrosTransicion,
    SalidaControl,
    SensoresNave,
    Tensor,
    control_transicion_metrica,
)
from einstein_proxy import T_from_g
from metricas_motor import InjectionSite, metrics_in_ship_chart
from presupuesto_energia import evaluar_presupuesto
from control_motor import tasa_lastre_desde_dpsi, frecuencia_anillos_desde_psi
from tau_crit import SenalCausal, detectar_tau_crit, evaluar_estado_causal
from transicion_metrica import dpsi_dtau, psi, z_phase


class Fase(Enum):
    CALIBRACION = auto()       # Fase 0 — Nave A, Minkowski
    DESCENSO = auto()          # Fase 1 — ergósfera pasiva
    INYECCION_CTC = auto()     # Fase 2 — anillos + Penrose
    RUPTURA_TOPOLOGICA = auto()  # Fase 3 — rampa ψ
    EXTRACCION = auto()        # post-burbuja, retorno al faro
    ABORT = auto()


@dataclass
class TelemetriaNaveA:
    reloj_beacon: float = 1.0
    enlace_activo: bool = True
    coordenadas_ok: bool = True


@dataclass
class ComandoMotor:
    fase: Fase
    frecuencia_anillos_hz: float = 0.0
    tasa_lastre_kg_s: float = 0.0
    inyeccion: Tensor = field(default_factory=Tensor)
    ruptura_emergencia: bool = False
    modo_compensacion_z: bool = False
    mensaje: str = ""


@dataclass
class ConfigMotor:
    site: InjectionSite = field(default_factory=InjectionSite)
    par: ParametrosTransicion = field(default_factory=ParametrosTransicion)
    usar_T_desde_g: bool = True
    auto_tau_crit: bool = True


class MotorCausal:
    def __init__(self, config: ConfigMotor | None = None) -> None:
        self.cfg = config or ConfigMotor()
        self.fase = Fase.CALIBRACION
        self.pid = PIDAdaptativo()
        self.tau_crit_locked: float | None = None
        self.T_medido = Tensor()
        self._pasos = 0
        self._beacon = TelemetriaNaveA()

    def set_beacon(self, beacon: TelemetriaNaveA) -> None:
        self._beacon = beacon

    def _tau_crit(self) -> float:
        return self.tau_crit_locked if self.tau_crit_locked is not None else self.cfg.par.tau_crit

    def transicion(self, nueva: Fase, msg: str = "") -> None:
        self.fase = nueva
        self._ultimo_msg = msg

    def paso(self, tau: float, sensores: SensoresNave | None = None) -> ComandoMotor:
        self._pasos += 1
        site = self.cfg.site
        par = self.cfg.par
        z = z_phase(tau, self._tau_crit(), par.delta_tau)
        causal = evaluar_estado_causal(site, tau, self._tau_crit(), par.delta_tau)

        if sensores is None:
            from control_motor import sensores_desde_metrica

            sensores = sensores_desde_metrica(site, tau, par)

        cmd = ComandoMotor(fase=self.fase)

        # --- Fase 0: calibración con Nave A ---
        if self.fase == Fase.CALIBRACION:
            if not self._beacon.enlace_activo or not self._beacon.coordenadas_ok:
                self.transicion(Fase.ABORT, "pérdida de faro Nave A")
            elif self._pasos >= 1 and tau > par.tau_crit - 1.5 * par.delta_tau:
                self.transicion(Fase.DESCENSO, "faro OK, inicio descenso")
            cmd.mensaje = "sincronizando reloj con Nave A"
            cmd.frecuencia_anillos_hz = 0.0
            return self._finalize(cmd)

        # --- Fase 1: descenso pasivo ---
        if self.fase == Fase.DESCENSO:
            if causal.senal in (SenalCausal.ERGOSFERA, SenalCausal.CONO_CERRADO):
                self.transicion(Fase.INYECCION_CTC, "ergósfera alcanzada")
            cmd.mensaje = "propulsión principal apagada"
            return self._finalize(cmd)

        # --- Fase 2: CTC + Penrose ---
        if self.fase == Fase.INYECCION_CTC:
            dpsi = dpsi_dtau(tau, self._tau_crit(), par.delta_tau)
            cmd.tasa_lastre_kg_s = tasa_lastre_desde_dpsi(dpsi)
            cmd.frecuencia_anillos_hz = frecuencia_anillos_desde_psi(psi(z))
            if self.cfg.auto_tau_crit and causal.senal == SenalCausal.INVERSION_TEMPORAL:
                self.tau_crit_locked = tau
                self.transicion(Fase.RUPTURA_TOPOLOGICA, f"tau_crit detectado en tau={tau:.4f}")
            elif tau >= self._tau_crit():
                self.transicion(
                    Fase.RUPTURA_TOPOLOGICA,
                    f"handover programado en tau_crit={self._tau_crit():.4f}",
                )
            pb = evaluar_presupuesto(site, self._tau_crit(), par.delta_tau)
            if not pb.viable and self._pasos > 5:
                self.transicion(Fase.ABORT, "presupuesto energetico no viable")
            cmd.mensaje = f"Penrose lastre={cmd.tasa_lastre_kg_s:.2f} kg/s"
            if self.fase == Fase.RUPTURA_TOPOLOGICA:
                pass  # cae al bloque Fase 3 en el mismo paso
            else:
                return self._finalize(cmd)

        # --- Fase 3 / extracción: control ψ + PID ---
        if self.fase in (Fase.RUPTURA_TOPOLOGICA, Fase.EXTRACCION):
            g_k, g_a = metrics_in_ship_chart(site)
            if self.cfg.usar_T_desde_g:
                t_k, t_a = T_from_g(g_k), T_from_g(g_a)
            else:
                from control_motor import T_alcubierre_nominal, T_kerr_nominal

                t_k, t_a = T_kerr_nominal(), T_alcubierre_nominal()

            out: SalidaControl = control_transicion_metrica(
                z, tau, sensores, self.T_medido, self.pid, par, t_k, t_a
            )
            self.T_medido.rho += 0.25 * (out.inyeccion_aplicada.rho - self.T_medido.rho)

            cmd.frecuencia_anillos_hz = out.frecuencia_anillos_hz
            cmd.tasa_lastre_kg_s = out.tasa_lastre_kg_s
            cmd.inyeccion = out.inyeccion_aplicada
            cmd.ruptura_emergencia = out.ruptura_emergencia
            cmd.modo_compensacion_z = out.modo_compensacion_z

            if self.fase == Fase.RUPTURA_TOPOLOGICA and abs(z) >= 1.0:
                self.transicion(Fase.EXTRACCION, "rampa ψ completada")
            cmd.mensaje = f"control ψ z={z:.3f} senal={causal.senal.name}"

        if self.fase == Fase.ABORT:
            cmd.mensaje = "ABORT — escudo Alcubierre forzado"
            cmd.ruptura_emergencia = True

        return self._finalize(cmd)

    def _finalize(self, cmd: ComandoMotor) -> ComandoMotor:
        cmd.fase = self.fase
        return cmd

    def calibrar_tau_crit(self, tau_grid: list[float]) -> float:
        tc = detectar_tau_crit(
            self.cfg.site, tau_grid, self.cfg.par.delta_tau, self.cfg.par.tau_crit
        )
        self.tau_crit_locked = tc
        self.cfg.par.tau_crit = tc
        return tc
