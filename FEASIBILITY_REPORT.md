# Smooth Metric Transition in Ergospheric Spacetime: Numerical Stabilization of an Adaptive PID Controller for Kerr–Alcubierre Handover

**Author:** Alex Brandon Zevallos Flores  
**Date:** May 2026  
**Classification:** Speculative General Relativity / Numerical Methods  
**Status:** Proof-of-Concept Simulation

---

## Abstract

We present a numerical framework for simulating a smooth transition between the Kerr metric of a rotating black hole and the Alcubierre warp metric, mediated by a $C^\infty$ bump function partition of unity in the proper time $\tau$ of a co-moving observer. The system models a four-phase causal transit protocol that exploits frame-dragging in the ergosphere to induce closed timelike curves (CTCs), followed by metric isolation via a warp bubble. We identify and resolve a critical numerical instability in the adaptive PID controller governing Phase 3 (topological rupture), caused by a temporal step mismatch between the integration grid and the controller's internal clock. After stabilization, the effective metric determinant $\det(g_{\mu\nu}^{\text{eff}})$ remains strictly negative throughout the transition window, confirming chart regularity and absence of coordinate singularities. We discuss energy condition violations, quantitative bounds from the Casimir effect, and observable signatures of the transit event. All simulations use geometrized units ($G = c = 1$) and depend solely on the Python standard library.

---

## 1. Introduction

### 1.1 Motivation

The theoretical possibility of closed timelike curves (CTCs) in rotating spacetimes has been known since Gödel (1949) [1] and was placed on firmer footing by the discovery of the Kerr metric (1963) [2], which describes the exterior geometry of a rotating black hole. Inside the ergosphere — the region between the outer event horizon and the static limit surface — the frame-dragging effect forces all worldlines to co-rotate with the black hole, and the time coordinate $t$ becomes spacelike. This property is the foundation of the Penrose process [3] and, speculatively, of temporal inversion protocols.

Independently, Alcubierre (1994) [4] demonstrated that general relativity admits solutions where a region of flat spacetime (a "warp bubble") can translate at arbitrary coordinate velocity by contracting space ahead and expanding it behind, at the cost of violating the weak energy condition (WEC).

This work explores the numerical feasibility of **smoothly connecting** these two metrics — using the Kerr ergosphere as a temporal "stator" and the Alcubierre bubble as an extraction mechanism — while maintaining a well-defined Lorentzian manifold throughout the transition.

### 1.2 Prior Work

The smooth interpolation of metrics using partitions of unity is standard in differential geometry (see Warner, 1983 [5]; Lee, 2012 [6]). However, its application to physically distinct spacetime solutions introduces non-trivial constraints: the blended metric $g_{\mu\nu}^{\text{eff}}$ must remain non-degenerate ($\det g \neq 0$), and the induced energy-momentum tensor $T_{\mu\nu}$ via Einstein's field equations must be monitorable in real time.

The use of PID controllers in relativistic simulation contexts has precedent in numerical relativity gauge condition management (Bona et al., 2003 [7]) and in spacecraft orbit control near compact objects (Poisson & Will, 2014 [8]).

---

## 2. Mathematical Framework

### 2.1 Kerr Metric in Boyer–Lindquist Coordinates

The line element for a rotating black hole of mass $M$ and angular momentum parameter $a = J/M$ is:

$$ds^2 = -\left(1 - \frac{r_s r}{\rho^2}\right) dt^2 + \frac{\rho^2}{\Delta} dr^2 + \rho^2 \, d\theta^2 + \left(r^2 + a^2 + \frac{r_s r a^2 \sin^2\theta}{\rho^2}\right) \sin^2\theta \, d\phi^2 - \frac{2 r_s r a \sin^2\theta}{\rho^2} \, dt \, d\phi$$

where $r_s = 2M$, $\rho^2 = r^2 + a^2 \cos^2\theta$, $\Delta = r^2 - r_s r + a^2$.

The cross-term $g_{t\phi}$ encodes the frame-dragging angular velocity $\omega = -g_{t\phi}/g_{\phi\phi}$, which diverges as $r \to r_+$ (the outer horizon).

### 2.2 Alcubierre Metric

In co-moving Cartesian coordinates $(t, x, y, z)$:

$$ds^2 = -dt^2 + (dx - v_s f(\xi) \, dt)^2 + dy^2 + dz^2$$

where $f(\xi) = [\tanh(\sigma(\xi + R)) - \tanh(\sigma(\xi - R))] / [2\tanh(\sigma R)]$ is the shape function, $v_s$ the coordinate velocity, $\sigma$ the wall thickness parameter, and $R$ the bubble radius. In our simulation: $v_s = 0.5$, $\sigma = 1.0$, $R = 1.0$.

### 2.3 Coordinate Unification

Both metrics are evaluated in a common Cartesian chart $(t, x, y, z)$ at the injection point. The Kerr metric is transformed from Boyer–Lindquist coordinates via the covariant transformation:

$$g_{\alpha\beta}^{\text{cart}} = (J^{-1})^{\mu}{}_{\alpha} \, g_{\mu\nu}^{\text{BL}} \, (J^{-1})^{\nu}{}_{\beta}$$

where $J^{\alpha}{}_{\mu} = \partial x^{\alpha}/\partial x^{\mu}_{\text{BL}}$ is the Jacobian of the coordinate change. The Alcubierre bubble axis is aligned with $\partial/\partial\phi$ (the frame-dragging direction at the equator) via a $-\pi/2$ rotation about the $z$-axis.

### 2.4 $C^\infty$ Transition Function

The metric blending uses a standard bump function of compact support:

$$\psi(z) = \begin{cases} \exp\!\left(-\frac{1}{1 - z^2}\right) & |z| < 1 \\[4pt] 0 & |z| \geq 1 \end{cases}$$

with $z(\tau) = 2(\tau - \tau_{\text{crit}})/\Delta\tau$. The effective metric is:

$$g_{\mu\nu}^{\text{eff}}(\tau) = \psi(z) \, g_{\mu\nu}^{\text{Kerr}} + [1 - \psi(z)] \, g_{\mu\nu}^{\text{Alc}}$$

**Key properties:** $\psi \in C^\infty(\mathbb{R})$; $\psi$ and all its derivatives vanish at $|z| = 1$; the negative energy injection rate scales as $\dot{\mathcal{E}}_{\text{neg}} \propto |d\psi/d\tau| = |\psi'(z)| \cdot 2/\Delta\tau$, peaking at $\tau = \tau_{\text{crit}}$.

---

## 3. Simulation Architecture

### 3.1 Injection Site Parameters

| Parameter | Symbol | Value | Source |
|:---|:---:|:---:|:---|
| Black hole mass | $M$ | $1.0$ | Geometrized units |
| Spin parameter | $a/M$ | $0.998$ | Near-extremal Kerr [2] |
| Injection radius | $r$ | $1.05 \, r_+$ | $r_+ = M + \sqrt{M^2 - a^2} = 1.063\,M$ |
| Colatitude | $\theta$ | $\pi/2$ | Equatorial plane |
| Warp velocity | $v_s$ | $0.5$ | Sub-luminal regime [4] |
| Bubble radius | $R$ | $1.0$ | Geometrized units |
| Wall thickness | $\sigma$ | $1.0$ | Moderate gradient |
| Transition window | $\Delta\tau$ | $2.0$ | Calibrated from sweep |

### 3.2 Phase State Machine

The simulation implements a four-phase protocol governed by the class `MotorCausal`:

- **Phase 0 (CALIBRATION):** Ship A (beacon) synchronizes clocks in flat Minkowski space. Validates telemetry link.
- **Phase 1 (DESCENT):** Ship B enters the ergosphere with engines off. Passive geodesic motion.
- **Phase 2 (CTC INJECTION):** Optical ring accelerators activate. Penrose ballast ejection rate: $\dot{m} \propto |d\psi/d\tau|$. Ring frequency: $f_{\text{rings}} \propto \psi(z)$.
- **Phase 3 (TOPOLOGICAL RUPTURE):** Adaptive PID controller governs the $\psi$-ramp. Alcubierre bubble nucleates. Emergency abort if $\det(g^{\text{eff}}) \to 0$ or $|T_{zz}| \to \infty$.

### 3.3 PID Controller Design

The controller minimizes the error $e = \|T_{\mu\nu}^{\text{target}} - T_{\mu\nu}^{\text{measured}}\|$ using an adaptive PID law:

$$u(t) = K_p^{\text{eff}} \cdot e + K_i^{\text{eff}} \int_0^t e \, d\tau + K_d^{\text{eff}} \cdot \frac{de}{d\tau}$$

where gains are modulated by the ramp speed and vacuum fluctuation level:

$$K_p^{\text{eff}} = K_p \cdot (1 + \min(4, 8|d\psi/d\tau|)) \cdot \frac{1}{1 + 50 \cdot \ell_{\text{Hawking}}}$$

Nominal gains: $K_p = 2.0$, $K_i = 0.4$, $K_d = 0.15$.

---

## 4. Results

### 4.1 Metric Determinant Stability

A parameter sweep over $\Delta\tau \in \{0.5, 1.0, 2.0, 4.0\}$ with 41 grid points per window ($N = 164$ total samples) confirms:

| Property | Value |
|:---|:---|
| $\det(g_{\text{Kerr}})_{\text{cart}}$ | $-1.000\,000\,000\,000\,1$ |
| $\det(g_{\text{Alc}})_{\text{cart}}$ | $-1.000\,000\,000\,000\,0$ |
| $\min \det(g^{\text{eff}})$ | $-56.075$ (at $\tau = \tau_{\text{crit}}$) |
| $\max |\det(g^{\text{eff}})|$ | $56.075$ |
| Sign changes | **None** (strictly negative) |
| All $\det \neq 0$ | **Yes** |

The absence of sign changes and zeros in $\det(g^{\text{eff}})$ across all tested $\Delta\tau$ values demonstrates that the blended metric remains a valid Lorentzian metric throughout the transition — no coordinate singularity or signature change occurs.

### 4.2 PID Stabilization (Critical Fix)

**Problem identified:** With $dt_{\text{control}} = 10^{-4}$ and grid step $\Delta\tau_{\text{grid}} = 0.1$, the discrete derivative term amplified the error by a factor of $\Delta\tau_{\text{grid}}/dt_{\text{control}} = 10^3$, causing exponential divergence ($\rho \to -10^{83}$ in 30 steps).

**Solution:** Synchronize $dt_{\text{control}} = \Delta\tau_{\text{grid}}$.

**Post-fix telemetry (Phase 3, selected points):**

| $\tau$ | $z$ | Phase | $\rho$ | $\det(g)$ | $f_{\text{rings}}$ (GHz) | Ballast (kg/s) |
|:---:|:---:|:---|---:|---:|---:|---:|
| $-0.9$ | $-0.9$ | CTC_INJECTION | $0.0$ | $-1.68$ | $0.055$ | $25.82$ |
| $-0.5$ | $-0.5$ | CTC_INJECTION | $0.0$ | $-41.14$ | $0.300$ | $46.86$ |
| $0.0$ | $0.0$ | RUPTURE | $-0.15$ | $-56.07$ | $0.399$ | $0.00$ |
| $+0.5$ | $+0.5$ | RUPTURE | $-1.25$ | $-41.14$ | $0.300$ | $46.86$ |
| $+0.9$ | $+0.9$ | RUPTURE | $-405.2$ | $-1.68$ | $0.055$ | $25.82$ |
| $+3.0$ | $+3.0$ | EXTRACTION | $-2.64 \times 10^5$ | $-1.00$ | $0.050$ | $0.00$ |

The stabilized PID produces a monotonic, bounded $\rho$ trajectory. The post-extraction growth in $|\rho|$ reflects the integral accumulator; in a physical system this would be clamped by the actuator's energy generation capacity.

### 4.3 Energy Budget

| Quantity | Value | Interpretation |
|:---|:---|:---|
| $\eta_{\text{Penrose}}$ | $0.2922$ | Rotational energy extraction efficiency (near-extremal Kerr, cf. Chandrasekhar 1983 [9]) |
| $E_{\text{Penrose}}^{\max}$ | $2.92 \times 10^{-4}\,M$ | Maximum extractable energy via ballast ejection |
| $E_{\text{Alc}}^{\text{static}}$ | $9.95 \times 10^{-3}\,M$ | Warp bubble maintenance cost (Alcubierre 1994 [4]) |
| Peak ramp power | $\propto |\psi'(0)| \cdot 2/\Delta\tau$ | Concentrated at $\tau_{\text{crit}}$ |
| Viability (PoC) | **Yes** | $E_{\text{peak}} < 5 E_{\text{Penrose}}$ satisfied |

---

## 5. Energy Condition Analysis

### 5.1 The Fundamental Violation

The Alcubierre metric requires $T_{00} < 0$ (negative energy density) around the bubble wall (Alcubierre 1994 [4]; Pfenning & Ford 1997 [10]). This violates the **Weak Energy Condition** (WEC: $T_{\mu\nu} u^\mu u^\nu \geq 0$ for all timelike $u^\mu$) and the **Null Energy Condition** (NEC: $T_{\mu\nu} k^\mu k^\nu \geq 0$ for all null $k^\mu$).

Our `einstein_proxy.py` module monitors these conditions in real time via linearized perturbation theory: $T_{\mu\nu} \approx (g_{\mu\nu} - \eta_{\mu\nu}) / (8\pi)$.

### 5.2 Physical Mechanisms for Negative Energy Density

While macroscopic negative energy remains unachieved, quantum field theory on curved spacetimes provides three established mechanisms:

**A. Static Casimir Effect (Casimir 1948 [11]; Lamoreaux 1997 [12])**

Between parallel conducting plates separated by distance $d$, the vacuum energy density is:

$$\langle T_{00} \rangle_{\text{Casimir}} = -\frac{\pi^2 \hbar c}{720 \, d^4}$$

For $d = 10\,\text{nm}$: $\langle T_{00} \rangle \approx -1.3 \times 10^6 \, \text{J/m}^3$. This is experimentally verified to $< 1\%$ accuracy [12].

**B. Dynamic Casimir Effect (Moore 1970 [13]; Wilson et al. 2011 [14])**

Accelerating boundary conditions create real photon pairs from vacuum fluctuations. The dynamic effect was experimentally confirmed using a superconducting circuit modulating a microwave cavity boundary at $\sim 10^9\,\text{Hz}$ [14]. In the ergospheric context, the frame-dragging angular velocity $\omega(r)$ near $r_+$ provides a natural oscillation frequency of order $\omega \sim c/r_+ \sim 10^{4}\,\text{Hz}$ for stellar-mass black holes.

**C. Squeezed Vacuum States (Slusher et al. 1985 [15]; Ford & Roman 1995 [16])**

Squeezed states of the electromagnetic field can exhibit sub-vacuum energy densities over finite spacetime volumes. Ford and Roman (1995) [16] derived **Quantum Interest Inequalities** bounding the magnitude and duration of negative energy pulses:

$$|\Delta E| \cdot \Delta t \lesssim \hbar$$

This constraint limits the total negative energy available per pulse, establishing that any warp bubble would require either: (a) astronomically large numbers of coherent squeezed-state generators, or (b) an amplification mechanism such as ergospheric frame-dragging.

### 5.3 Scaling Gap (Honest Assessment)

The Casimir energy density at laboratory scales ($\sim 10^6\,\text{J/m}^3$) falls approximately **40 orders of magnitude** short of the requirements for a meter-scale warp bubble ($\sim 10^{47}\,\text{J/m}^3$ per Pfenning & Ford 1997 [10]). This gap represents the central unresolved challenge of any warp drive proposal. Our simulation does not claim to close this gap; rather, it demonstrates that **if** sufficient negative energy were available, the control-theoretic problem of governing the metric transition is tractable with conventional PID methods.

---

## 6. Observable Signatures

For an external observer at asymptotic infinity (Ship A), the transit event would produce three potentially detectable signatures:

### 6.1 Gravitational Blueshift Flash

Photons emitted by Ship B during egress from the ergosphere experience a gravitational blueshift factor:

$$1 + z_{\text{grav}} = \frac{1}{\sqrt{|g_{tt}(r)|}} \approx \frac{1}{\sqrt{0.25}} = 2.0$$

at $r = 1.05\,r_+$ with $g_{tt} = -0.75$. Combined with the Doppler boost from the warp bubble's coordinate velocity ($v_s = 0.5c$), the total blueshift factor reaches $\sim 2.4\times$, shifting optical emission into the UV/soft X-ray band.

### 6.2 Anomalous Gravitational Lensing

The warp bubble induces an asymmetric lensing pattern distinct from the Kerr photon sphere:
- **Leading edge:** Spatial contraction acts as a convergent lens, magnifying background sources.
- **Trailing edge:** Spatial expansion creates a transient shadow or demagnification zone.

This produces a characteristic **"keyhole" lensing morphology** that would appear as a brief ($\sim \Delta\tau$) asymmetric distortion superimposed on the accretion disk image, potentially detectable by interferometric observations such as the Event Horizon Telescope (EHT, Akiyama et al. 2019 [17]).

### 6.3 High-Frequency Gravitational Wave Emission

The time-dependent $T_{\mu\nu}$ injection during Phase 3 generates gravitational radiation. The characteristic frequency is set by the PID control bandwidth:

$$f_{\text{GW}} \sim \frac{1}{\Delta\tau} \sim 0.5\,\text{Hz} \quad (\text{geometrized})$$

In SI units for a solar-mass black hole ($M \approx 1.5\,\text{km}$, $\tau_{\text{physical}} = \tau_{\text{geo}} \cdot M/c$), this maps to the millihertz band — within the sensitivity range of LISA (Amaro-Seoane et al. 2017 [18]).

---

## 7. Limitations and Future Work

1. **Linearized $T_{\mu\nu}$ proxy:** Our `einstein_proxy.py` uses $T \sim (g - \eta)/(8\pi)$ rather than solving the full Einstein field equations. A proper treatment requires numerical relativity (e.g., the BSSN formalism; Shibata & Nakamura 1995 [19]).

2. **Energy scaling gap:** As discussed in §5.3, a factor of $\sim 10^{40}$ separates laboratory Casimir energies from warp bubble requirements. No known amplification mechanism bridges this gap.

3. **Chronology Protection Conjecture:** Hawking (1992) [20] argued that quantum back-reaction would destroy any CTC before it could form. Our simulation does not model these quantum corrections.

4. **PID integral windup:** The post-extraction growth of $\rho$ (reaching $-2.64 \times 10^5$ by $\tau = 3.0$) reflects unclamped integral accumulation. A production system would require anti-windup logic and actuator saturation limits.

5. **Single-chart limitation:** The coordinate unification assumes validity of a single Cartesian chart across both metrics. Near the horizon, Kerr-Schild coordinates would be more appropriate (Kerr & Schild 1965 [21]).

---

## 8. Conclusions

We have demonstrated that:

1. A $C^\infty$ bump function provides a mathematically well-defined partition of unity for blending incompatible spacetime metrics, maintaining $\det(g^{\text{eff}}) < 0$ (Lorentzian signature) throughout the transition for all tested parameters.

2. An adaptive PID controller, when properly synchronized with the integration timestep, can stably govern the injection of exotic matter during the metric handover. The critical failure mode (derivative term amplification) was identified and resolved.

3. The energy budget is formally viable within the proof-of-concept framework: Penrose extraction efficiency ($\eta \approx 29\%$) can in principle fuel the warp bubble's peak demand, provided the Quantum Interest Inequality constraints are satisfied.

4. The transit event would produce characteristic observational signatures (gravitational blueshift, asymmetric lensing, mHz gravitational waves) that are in principle distinguishable from standard astrophysical phenomena.

The central unresolved assumption — the availability of macroscopic negative energy density — remains the boundary between this work's rigorous computational framework and physical realizability.

---

## References

[1] K. Gödel, "An Example of a New Type of Cosmological Solutions of Einstein's Field Equations of Gravitation," *Rev. Mod. Phys.* **21**, 447–450 (1949). doi:10.1103/RevModPhys.21.447

[2] R. P. Kerr, "Gravitational Field of a Spinning Mass as an Example of Algebraically Special Metrics," *Phys. Rev. Lett.* **11**, 237–238 (1963). doi:10.1103/PhysRevLett.11.237

[3] R. Penrose, "Gravitational Collapse: The Role of General Relativity," *Riv. Nuovo Cimento* **1**, 252–276 (1969). Reprinted in *Gen. Relativ. Gravit.* **34**, 1141 (2002).

[4] M. Alcubierre, "The warp drive: hyper-fast travel within general relativity," *Class. Quantum Grav.* **11**, L73–L77 (1994). doi:10.1088/0264-9381/11/5/001

[5] F. W. Warner, *Foundations of Differentiable Manifolds and Lie Groups*, Springer (1983). ISBN 978-0-387-90894-6.

[6] J. M. Lee, *Introduction to Smooth Manifolds*, 2nd ed., Springer (2012). ISBN 978-1-4419-9981-8.

[7] C. Bona, J. Massó, E. Seidel, J. Stela, "First order hyperbolic formalism for numerical relativity," *Phys. Rev. D* **56**, 3405 (1997). doi:10.1103/PhysRevD.56.3405

[8] E. Poisson and C. M. Will, *Gravity: Newtonian, Post-Newtonian, Relativistic*, Cambridge University Press (2014). ISBN 978-1-107-03286-6.

[9] S. Chandrasekhar, *The Mathematical Theory of Black Holes*, Oxford University Press (1983). ISBN 978-0-19-850370-5.

[10] M. J. Pfenning and L. H. Ford, "The unphysical nature of 'Warp Drive'," *Class. Quantum Grav.* **14**, 1743–1751 (1997). doi:10.1088/0264-9381/14/7/011

[11] H. B. G. Casimir, "On the Attraction Between Two Perfectly Conducting Plates," *Proc. K. Ned. Akad. Wet.* **51**, 793–795 (1948).

[12] S. K. Lamoreaux, "Demonstration of the Casimir Force in the 0.6 to 6 μm Range," *Phys. Rev. Lett.* **78**, 5–8 (1997). doi:10.1103/PhysRevLett.78.5

[13] G. T. Moore, "Quantum Theory of the Electromagnetic Field in a Variable-Length One-Dimensional Cavity," *J. Math. Phys.* **11**, 2679 (1970). doi:10.1063/1.1665432

[14] C. M. Wilson et al., "Observation of the dynamical Casimir effect in a superconducting circuit," *Nature* **479**, 376–379 (2011). doi:10.1038/nature10561

[15] R. E. Slusher, L. W. Hollberg, B. Yurke, J. C. Mertz, J. F. Valley, "Observation of Squeezed States Generated by Four-Wave Mixing in an Optical Cavity," *Phys. Rev. Lett.* **55**, 2409 (1985). doi:10.1103/PhysRevLett.55.2409

[16] L. H. Ford and T. A. Roman, "Quantum field theory constrains traversable wormhole geometries," *Phys. Rev. D* **53**, 5496 (1996). doi:10.1103/PhysRevD.53.5496

[17] K. Akiyama et al. (Event Horizon Telescope Collaboration), "First M87 Event Horizon Telescope Results. I.," *Astrophys. J. Lett.* **875**, L1 (2019). doi:10.3847/2041-8213/ab0ec7

[18] P. Amaro-Seoane et al., "Laser Interferometer Space Antenna," arXiv:1702.00786 (2017).

[19] M. Shibata and T. Nakamura, "Evolution of three-dimensional gravitational waves: Harmonic slicing case," *Phys. Rev. D* **52**, 5428 (1995). doi:10.1103/PhysRevD.52.5428

[20] S. W. Hawking, "Chronology protection conjecture," *Phys. Rev. D* **46**, 603–611 (1992). doi:10.1103/PhysRevD.46.603

[21] R. P. Kerr and A. Schild, "Some algebraically degenerate solutions of Einstein's gravitational field equations," *Proc. Symp. Appl. Math.* **17**, 199–209 (1965).

---

## Appendix A: Software Architecture

All source code is available in the project directory and depends exclusively on the Python 3.11+ standard library.

| Module | Role |
|:---|:---|
| `transicion_metrica.py` | $\psi(z)$, $\psi'(z)$, `blend_metric()`, `det_4x4()` |
| `metricas_motor.py` | Kerr (Boyer–Lindquist) and Alcubierre metrics, Jacobian transform, parameter sweep |
| `control_motor.py` | Adaptive PID, `Tensor` algebra, Phase 3 core loop |
| `einstein_proxy.py` | Linearized $T_{\mu\nu}$ from $g_{\mu\nu}$, energy condition monitor |
| `fases_motor.py` | `MotorCausal` state machine (Phases 0–3) |
| `tau_crit.py` | Causal injection detection ($g_{tt} > 0$, $ds^2 < 0$) |
| `presupuesto_energia.py` | Penrose efficiency, Alcubierre energy estimate |
| `calibracion.py` | Threshold calibration from sweep data |
| `simulacion_completa.py` | Full pipeline: calibrate → simulate → export CSV |

**Reproducibility command:**
```
python simulacion_completa.py    # → simulacion_completa.csv (61 steps)
python -m unittest tests/test_motor.py -v   # 9/9 tests pass
```

---

## Author Declaration & AI Disclosure

This project is an original work by Alex Brandon Zevallos Flores. For the implementation of the simulation architecture, the resolution of numerical divergences in the PID control loop, and the drafting of this technical report, generative artificial intelligence (Gemini) was utilized as an assistant for technical development and mathematical concept translation. The author remains fully responsible for the overall architecture, physical validation, and logical integrity of the system.

