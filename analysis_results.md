# Physical Feasibility and Geodesic Trajectory Analysis in Kerr-Alcubierre Spacetime

This document presents the physical evaluation and numerical diagnostics of geodesic simulations in a dynamic spacetime transitioning between the Kerr metric (rotational gravitational field) and the Alcubierre metric (local warp deformation).

---

## 1. Spacetime Geometry and C^∞ Transition

The coupling between the Kerr metric ($g_{\mu\nu}^{\text{Kerr}}$) and the Alcubierre metric ($g_{\mu\nu}^{\text{Alcubierre}}$) is modeled using a smooth transition factor based on a $C^\infty$ bump function:

$$g_{\mu\nu}^{\text{eff}}(t, x, y, z) = \psi(t) g_{\mu\nu}^{\text{Kerr}}(x, y, z) + (1 - \psi(t)) g_{\mu\nu}^{\text{Alcubierre}}(t, x, y, z)$$

The transition function is defined with compact support in the coordinate time domain:

$$\psi(t) = \begin{cases} e^{-\frac{1}{1-z^2}} & \text{if } |z| < 1 \\ 0 & \text{if } |z| \ge 1 \end{cases}$$

where the dimensionless temporal phase parameter is defined as:

$$z = \frac{2(t - t_{\text{crit}})}{\Delta t}$$

This formulation guarantees that the blended metric remains infinitely differentiable ($C^\infty$) across all points of the spacetime manifold, preventing non-physical discontinuities in the stress-energy tensor $T_{\mu\nu}$ that would otherwise require instantaneous infinite energy densities.

---

## 2. Geodesic Integrator Formulation

To trace the propagation of light rays and test particles, we solve the system of second-order coupled ordinary differential equations for geodesics:

$$\frac{d^2 x^\mu}{d \lambda^2} + \Gamma^\mu_{\alpha\beta} p^\alpha p^\beta = 0$$

where $p^\mu = \frac{dx^\mu}{d\lambda}$ is the momentum four-vector and $\lambda$ is the affine parameter along the trajectory.

### Numerical Christoffel Symbols
Due to the hybrid and dynamic nature of the coupled spacetime, the Christoffel symbols are calculated via numerical partial derivatives of the metric using second-order central finite differences:

$$\Gamma^\mu_{\alpha\beta} = \frac{1}{2} g^{\mu\sigma} \left( \partial_\alpha g_{\beta\sigma} + \partial_\beta g_{\alpha\sigma} - \partial_\sigma g_{\alpha\beta} \right)$$

$$\partial_\gamma g_{\alpha\beta} \approx \frac{g_{\alpha\beta}(x + h \hat{e}_\gamma) - g_{\alpha\beta}(x - h \hat{e}_\gamma)}{2h} \quad (h = 10^{-4})$$

### Metric Constraint Conservation
The physical consistency of the 4th-order Runge-Kutta (RK4) integrator with integration step $\Delta \lambda = 0.05$ is monitored at each step by evaluating the normalization error of the momentum four-vector:

$$\mathcal{E} = |g_{\mu\nu} p^\mu p^\nu - C|$$

where $C = 0$ for null geodesics (photons) and $C = -1$ for timelike geodesics (massive particles).

---

## 3. Quantitative Diagnostics and Numerical Results

The simulation runs reveal three distinct dynamic regimes:

### Regime A: Flat Space (Minkowski)
By setting the physical parameters to $M = 0$, $a = 0$, and $v_s = 0$, the baseline precision of the algorithm was verified:
*   **Spatial path deviation:** $< 10^{-16}$ (perfect straight line).
*   **Maximum constraint error $\mathcal{E}$:** $3.59 \times 10^{-14}$ (machine precision limit).
*   **Diagnostic:** The numerical Christoffel calculation and RK4 solver are consistent and stable.

### Regime B: Distant Metric Transitions ($y_0 \ge 3.0$ or Low-Mass Black Holes)
Simulating a dynamic transition with parameters $M = 1.0$, $a = 0.998$, $v_s = 0.5$, $t_{\text{crit}} = 5.0$, and $\Delta t = 6.0$, but restricting trajectories to remain away from the event horizon:
*   **Maximum constraint error $\mathcal{E}$ ($y_0 = 3.0$):** $2.61 \times 10^{-7}$
*   **Maximum constraint error $\mathcal{E}$ ($y_0 = 1.5, M=0.5$):** $3.65 \times 10^{-7}$
*   **Behavior:** We observe smooth light deflection due to the Kerr curvature followed by gravitational lensing redirection within the Alcubierre warp bubble without loss of physical accuracy in the integrator.

### Regime C: Proximity to the Event Horizon ($y_0 = 1.5, M=1.0$)
When a geodesic passes very close to the outer event horizon $r_+ \approx 1.06$:
*   **Maximum constraint error $\mathcal{E}$:** $1.47 \times 10^{1}$ (local numerical divergence).
*   **Physical-Numerical Diagnosis:** In standard Boyer-Lindquist coordinates, the radial Kerr metric component $g_{rr} = \frac{\rho^2}{\Delta}$ diverges at the horizon (where $\Delta \to 0$). As we approach this coordinate singularity, spatial gradients of the metric grow exponentially, causing the fixed finite-difference step ($h = 10^{-4}$) and the RK4 integrator to accumulate severe truncation errors.
*   **Theoretical Mitigation:** For trajectories that cross or graze the event horizon, it is necessary to reformulate the metric in horizon-penetrating, coordinate-singularity-free charts (such as Kerr-Schild or Painlevé-Gullstrand coordinates).

---

## 4. Conclusion and Theoretical Contributions

1.  **Coherent Blending Model:** The use of the $C^\infty$ bump function allows a continuous temporal transition of spacetime geometries in general relativity without introducing first-order coordinate singularities in the curvature tensor.
2.  **Ray-Tracing Validation:** The numerical geodesic simulation proves to be highly accurate (constraint errors on the order of $10^{-7}$) for trajectories outside the critical coordinate singularity zone of the Boyer-Lindquist horizon.
3.  **Physical Feasibility:** The geodesic paths demonstrate how the pure gravitational lens and frame-dragging effects of Kerr are smoothly replaced by the kinematic spatial warp bubble of the Alcubierre metric as $\psi(t) \to 0$.
