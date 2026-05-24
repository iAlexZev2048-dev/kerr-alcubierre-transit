# Ergosphere-Alcubierre Metric Transition & PID Control Simulation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20360989.svg)](https://doi.org/10.5281/zenodo.20360989)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains a high-fidelity numerical simulation framework for a speculative spacetime transition: a causal handover between a rotating **Kerr Black Hole Ergosphere** and a translating **Alcubierre Warp Bubble**.

The transition is mediated by a smooth $C^\infty$ partition of unity (bump function) in the proper time $\tau$ of a co-moving observer. A critical contribution of this codebase is the implementation and stabilization of an **adaptive PID controller** that regulates active metric expansion and contraction during Phase 3 (topological rupture), preventing coordinate singularities and ensuring chart regularity.

> **Cita de Honor / Credit Note:**
> Este proyecto se basa en los fundamentos teóricos establecidos por R.P. Kerr (1963) sobre métricas de agujeros negros en rotación y M. Alcubierre (1994) sobre propulsión métrica. Esta arquitectura SCT (Smooth Causal Transit) es un desarrollo independiente que aplica principios de control PID y funciones de partición $C^\infty$ para la estabilización numérica de estas soluciones.

For a detailed physical, mathematical, and numerical analysis of this system, refer to the accompanying paper: **[INFORME_VIABILIDAD.md](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/INFORME_VIABILIDAD.md)** (*English*).

---

## Physical & Numerical Concept

The simulation models a four-phase causal transit protocol:
1. **Calibration (Phase 0):** Establishes metric determinant baselines and parameters.
2. **Descent (Phase 1):** Moves the co-moving observer into the Kerr ergosphere to exploit frame-dragging ($\omega = -g_{t\phi}/g_{\phi\phi}$).
3. **Causal Injection (Phase 2):** Initiates closed timelike curve (CTC) coupling.
4. **Topological Rupture & Extraction (Phase 3 & 4):** Engages the Alcubierre warp metric while smoothly extinguishing the Kerr background. An adaptive PID controller regulates the warp bubble's velocity profile ($v_s$) to keep the effective metric determinant $\det(g_{\mu\nu}^{\text{eff}})$ strictly negative, preventing coordinate singularity.

---

## Software Architecture

This project is written entirely using the **Python Standard Library** (no external package dependencies) to maximize portability and longevity in archive systems like Zenodo.

| Module | Purpose |
| :--- | :--- |
| **[transicion_metrica.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/transicion_metrica.py)** | $C^\infty$ bump function $\psi(z)$, metric blending algebra, and $4 \times 4$ determinant math. |
| **[metricas_motor.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/metricas_motor.py)** | Kerr and Alcubierre metric implementations in a shared chart, coordinate transformations, and parameter sweeps. |
| **[control_motor.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/control_motor.py)** | Core adaptive PID controller logic with anti-windup, noise filtering, and step synchronization. |
| **[control_motor.cpp](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/control_motor.cpp)** / **[control_motor.hpp](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/control_motor.hpp)** | High-performance C++ mirror of the PID control loop. |
| **[einstein_proxy.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/einstein_proxy.py)** | Linearized Einstein tensor $G_{\mu\nu}$ and stress-energy $T_{\mu\nu}$ proxy to monitor energy conditions (WEC/SEC/DEC). |
| **[fases_motor.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/fases_motor.py)** | State machine managing transition phases (0 to 4) and safety interrupts. |
| **[tau_crit.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/tau_crit.py)** | Computes critical proper time thresholds for causal injection safety. |
| **[presupuesto_energia.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/presupuesto_energia.py)** | Penrose extraction efficiency and Alcubierre negative mass-energy requirements. |
| **[calibracion.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/calibracion.py)** | Calibrates control thresholds using simulation sweeps. |
| **[simulacion_completa.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/simulacion_completa.py)** | Orchestrates the entire pipeline from calibration to final simulation output. |
| **[visualizar_resultados.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/visualizar_resultados.py)** | Interactive GUI telemetry visualizer (built on Tkinter/Canvas, zero external requirements). |
| **[tests/test_motor.py](file:///c:/Users/alex_/Documents/ciencia%20&%20sci%20fi/tests/test_motor.py)** | Comprehensive unit test suite (9 test cases covering metrics, PID, and state transitions). |

---

## Execution & Quick Start

### 1. Run the Full Simulation
Execute the orchestration script. This runs parameter sweeps, calibrates thresholds, runs the 5-phase transition, and writes telemetry to `simulacion_completa.csv`:

```bash
python simulacion_completa.py
```

### 2. View Telemetry Plots
Launch the zero-dependency Tkinter UI to inspect metric determinants, coordinate velocities, control inputs, and energy conditions:

```bash
python visualizar_resultados.py
```

### 3. Run Unit Tests
Verify mathematical and logical consistency across all modules:

```bash
python -m unittest tests/test_motor.py -v
```

---

## Citation & Academic Attribution

If you use this simulation code or build upon the theoretical framework in your research, please cite it using the following metadata:

### BibTeX

```bibtex
@software{zevallos_flores_2026_kerr_alcubierre,
  author       = {Zevallos Flores, Alex Brandon},
  title        = {Smooth Metric Transition in Ergospheric Spacetime: Kerr-Alcubierre Handover Simulation},
  month        = may,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {1.0.0},
  doi          = {10.5281/zenodo.20360989},
  url          = {https://github.com/iAlexZev2048-dev/kerr-alcubierre-transit}
}
```

### APA
> Zevallos Flores, A. B. (2026). *Smooth Metric Transition in Ergospheric Spacetime: Kerr-Alcubierre Handover Simulation* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.20360989

---

## License
- The **source code** is licensed under the [MIT License](LICENSE).
- The **viability report** (`INFORME_VIABILIDAD.md`) is licensed under the [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/) license.

---

## Declaración de Autoría / Author Declaration

**Declaración de Autoría:** Este proyecto es una obra original de Alex Brandon Zevallos Flores. Para la implementación de la arquitectura de simulación, la resolución de divergencias en el lazo de control PID y la redacción de este informe técnico, se utilizó inteligencia artificial (Gemini) como herramienta de asistencia técnica y traducción de conceptos matemáticos. El autor es responsable de toda la arquitectura, la validación física y la integridad lógica del sistema.

**AI Disclosure:** This project is an original work by Alex Brandon Zevallos Flores. For the implementation of the simulation architecture, the resolution of numerical divergences in the PID control loop, and the drafting of this technical report, generative artificial intelligence (Gemini) was utilized as an assistant for technical development and mathematical concept translation. The author remains fully responsible for the overall architecture, physical validation, and logical integrity of the system.

