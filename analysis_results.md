# Análisis de Viabilidad Física y Trayectorias Geodésicas en el Espacio-Tiempo de Kerr-Alcubierre

Este documento presenta la evaluación física y el diagnóstico numérico de la simulación geodésica en un espacio-tiempo dinámico de transición métrica entre Kerr (campo gravitatorio rotacional) y Alcubierre (métrica de deformación local).

---

## 1. Geometría Espaciotemporal y Transición C^∞

El modelado del acoplamiento entre la métrica de Kerr ($g_{\mu\nu}^{\text{Kerr}}$) y la métrica de Alcubierre ($g_{\mu\nu}^{\text{Alcubierre}}$) se realiza mediante un factor de transición suave basado en una rampa $C^\infty$ (función bump):

$$g_{\mu\nu}^{\text{eff}}(t, x, y, z) = \psi(t) g_{\mu\nu}^{\text{Kerr}}(x, y, z) + (1 - \psi(t)) g_{\mu\nu}^{\text{Alcubierre}}(t, x, y, z)$$

La función de transición se define con soporte compacto en el dominio temporal:

$$\psi(t) = \begin{cases} e^{-\frac{1}{1-z^2}} & \text{si } |z| < 1 \\ 0 & \text{si } |z| \ge 1 \end{cases}$$

donde el parámetro adimensional de fase temporal es:

$$z = \frac{2(t - t_{\text{crit}})}{\Delta t}$$

Esta formulación asegura que la transición métrica sea derivable infinitas veces en todos los puntos de la variedad espaciotemporal, evitando discontinuidades no físicas en el tensor de energía-momento $T_{\mu\nu}$ que requerirían densidades de energía infinitas instantáneas.

---

## 2. Formulación del Integrador de Geodésicas

Para trazar la propagación de luz y partículas de prueba, se resuelve el sistema de ecuaciones diferenciales ordinarias de segundo orden de las geodésicas:

$$\frac{d^2 x^\mu}{d \lambda^2} + \Gamma^\mu_{\alpha\beta} p^\alpha p^\beta = 0$$

donde $p^\mu = \frac{dx^\mu}{d\lambda}$ es el cuadrivector de momentum y $\lambda$ es el parámetro afín de la trayectoria.

### Símbolos de Christoffel Numéricos
Debido a la naturaleza híbrida y dinámica del espacio-tiempo acoplado, los símbolos de Christoffel se calculan mediante derivadas parciales numéricas obtenidas por diferencias finitas centradas de segundo orden:

$$\Gamma^\mu_{\alpha\beta} = \frac{1}{2} g^{\mu\sigma} \left( \partial_\alpha g_{\beta\sigma} + \partial_\beta g_{\alpha\sigma} - \partial_\sigma g_{\alpha\beta} \right)$$

$$\partial_\gamma g_{\alpha\beta} \approx \frac{g_{\alpha\beta}(x + h \hat{e}_\gamma) - g_{\alpha\beta}(x - h \hat{e}_\gamma)}{2h} \quad (h = 10^{-4})$$

### Conservación de la Ligadura Métrica
La consistencia física del integrador Runge-Kutta de 4.º orden (RK4) con paso de integración $\Delta \lambda = 0.05$ se verifica en cada paso evaluando el error de la ligadura de normalización del cuadrivector momentum:

$$\mathcal{E} = |g_{\mu\nu} p^\mu p^\nu - C|$$

donde $C = 0$ para geodésicas nulas (fotones) y $C = -1$ para geodésicas temporales (partículas masivas).

---

## 3. Diagnóstico Cuantitativo y Resultados Numéricos

Los resultados de las simulaciones revelan tres regímenes dinámicos distintos:

### Régimen A: Espacio Plano (Minkowski)
Fijando los parámetros físicos a $M = 0$, $a = 0$ y $v_s = 0$, se verificó la precisión basal del algoritmo:
*   **Desviación espacial de la trayectoria:** $< 10^{-16}$ (línea recta perfecta).
*   **Error máximo de ligadura $\mathcal{E}$:** $3.59 \times 10^{-14}$ (precisión de máquina).
*   **Diagnóstico:** El método de Christoffel numérico y el integrador RK4 son consistentes y estables.

### Régimen B: Transición Métricas Distantes ($y_0 \ge 3.0$ o Agujeros Negros de Baja Masa)
Simulando una transición dinámica con $M = 1.0$, $a = 0.998$, $v_s = 0.5$, $t_{\text{crit}} = 5.0$ y $\Delta t = 6.0$, pero restringiendo las trayectorias para que no se acerquen al horizonte de sucesos:
*   **Error máximo de ligadura $\mathcal{E}$ ($y_0 = 3.0$):** $2.61 \times 10^{-7}$
*   **Error máximo de ligadura $\mathcal{E}$ ($y_0 = 1.5, M=0.5$):** $3.65 \times 10^{-7}$
*   **Comportamiento:** Se observa la deflexión de la luz debido a la curvatura de Kerr y su posterior redireccionamiento por la burbuja warp de Alcubierre sin pérdida de precisión física en el integrador.

### Régimen C: Proximidad al Horizonte de Sucesos ($y_0 = 1.5, M=1.0$)
Cuando la geodésica pasa muy cerca del horizonte de sucesos externo $r_+ \approx 1.06$:
*   **Error máximo de ligadura $\mathcal{E}$:** $1.47 \times 10^{1}$ (divergencia numérica local).
*   **Diagnóstico físico-numérico:** En coordenadas de Boyer-Lindquist, la componente radial de la métrica de Kerr $g_{rr} = \frac{\rho^2}{\Delta}$ diverge en el horizonte (donde $\Delta \to 0$). Al aproximarse a esta singularidad de coordenadas, los gradientes métricos crecen exponencialmente, provocando que el paso fijo de diferencias finitas ($h = 10^{-4}$) y el integrador RK4 acumulen errores severos.
*   **Solución teórica:** Para trayectorias que crucen o rocen el horizonte de sucesos, es necesario reformular la métrica en coordenadas libres de singularidades en el horizonte (como coordenadas de Kerr-Schild o coordenadas de Painlevé-Gullstrand).

---

## 4. Conclusión y Aportes Teóricos

1.  **Modelo de Acoplamiento Coherente:** El uso de la función bump $C^\infty$ permite la transición temporal continua de métricas en relatividad general sin generar discontinuidades de primer orden en el tensor de curvatura.
2.  **Validación del Trazado de Rayos:** La simulación geodésica numérica demuestra ser altamente precisa (errores de ligadura del orden de $10^{-7}$) para trayectorias fuera de la región crítica del horizonte de sucesos de Boyer-Lindquist.
3.  **Viabilidad Física:** Las geodésicas muestran cómo la influencia gravitacional pura de Kerr (lente gravitacional y arrastre de marco) es reemplazada gradualmente por la cinemática de la métrica de Alcubierre a medida que $\psi(t) \to 0$.
