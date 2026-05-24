# Documento Técnico de Diseño Conceptual

**Título de la Invención:** Sistema de Tránsito Causal mediante Acoplamiento de Ergósfera y Protocolo de Extracción Alcubierre  
**Clasificación Geométrica:** Topología de Colectores de Kerr / Métrica Espaciotemporal No Lineal  
**Estado:** Prueba de Concepto Teórica  
**Autor:** Alex Brandon Zevallos Flores  
**Fecha:** Mayo 2026  

---

## 1. Resumen de la Arquitectura

La presente topología describe un motor de alteración temporal macrodinámica. Resuelve el problema del colapso térmico y las fuerzas de marea destructivas de los Cilindros de Tipler aislando la carga biológica mediante un chasis de dos etapas. 

Utiliza la energía rotacional de la ergósfera de un agujero negro supermasivo como "estator" primario para inclinar los conos de luz (Arrastre de Marco), acoplado a una matriz de aceleradores ópticos en serie para forzar una Curva Cerrada de Tipo Tiempo (CTC). La extracción térmica del pozo gravitatorio se realiza mediante la ignición retardada de un motor de densidad de energía negativa (Burbuja de Alcubierre).

---

## 2. Marco Teórico y Fórmulas de Inyección

### 2.1. El Estator Natural (Métrica de Kerr)

El sistema se ancla en el límite estático de un agujero negro en rotación, donde el espacio-tiempo es forzado a co-rotar a velocidades superlumínicas relativas al infinito asintótico. La geometría exacta de esta región de inyección se define mediante la Métrica de Kerr:

$$ds^2 = -\left(1 - \frac{r_s r}{\rho^2}\right)c^2 dt^2 + \frac{\rho^2}{\Delta} dr^2 + \rho^2 d\theta^2 + \left(r^2 + a^2 + \frac{r_s r a^2}{\rho^2}\sin^2\theta\right)\sin^2\theta d\phi^2 - \frac{2r_s r a \sin^2\theta}{\rho^2} c dt d\phi$$

Donde:
*   $r_s = 2M$
*   $\rho^2 = r^2 + a^2 \cos^2\theta$
*   $\Delta = r^2 - r_s r + a^2$

El término cruzado $dt d\phi$ representa el diferencial de Arrastre de Marco, el combustible gravitatorio primario del sistema.

### 2.2. Sobrealimentación del Vórtice (Acoplamiento de Anillos)

Dentro de la ergósfera, el colector activa una serie de anillos láser continuos. Al circular fotones en un bucle cerrado, se induce un gradiente gravitacional secundario que cierra el ángulo del cono de luz de la nave $ds^2 < 0$, invirtiendo la coordenada temporal ($t$) respecto al espacio exterior.

---

## 3. Diagrama de Flujo Mecánico

*   **Fase 0: Calibración del Marco Inercial.** La Nave A (Faro de Referencia) se posiciona en el espacio de Minkowski plano ($r \to \infty$), donde el tensor de energía-impulso es nulo.
*   **Fase 1: Descenso Pasivo.** La Nave B (Carga Útil) ingresa a la ergósfera del estator masivo con propulsión apagada para evitar gasto termodinámico.
*   **Fase 2: Inyección de Tránsito Causal.** La Nave B ingresa al tubo de anillos acoplado en la ergósfera. Mediante el Proceso de Penrose, la nave extrae momento angular del agujero negro soltando masa de lastre en contra de la rotación, generando el delta-v ($\Delta v$) necesario para completar el circuito de Curva Cerrada de Tipo Tiempo sin encender motores principales.
*   **Fase 3: Ruptura Topológica (Extracción).** Una vez alcanzada la coordenada temporal negativa (el pasado), la Nave B inicializa la métrica de Alcubierre para aislar su chasis de la geometría de Kerr.

---

## 4. Protocolo de Aislamiento (Métrica de Alcubierre)

Para evitar que la carga útil sea absorbida por el Horizonte de Eventos, el sistema modifica el tensor $T_{\mu\nu}$ inyectando materia de densidad energética negativa local. La topología local se sobreescribe con el colector de Alcubierre:

$$ds^2 = -c^2 dt^2 + (dx - v_s f(r_s) dt)^2 + dy^2 + dz^2$$

*   **Contracción Frontal:** El espacio frente a la nave colapsa ($\theta < 0$).
*   **Expansión Trasera:** El espacio entre el chasis y el Horizonte de Eventos se expande métricamente ($\theta > 0$).
*   **Aislamiento Geométrico:** La Nave B entra en reposo cinemático absoluto y se desliza fuera del campo gravitatorio masivo de retorno hacia la coordenada balizada por la Nave A, burlando la gravedad térmica del sistema.

---

## 5. Transición Analítica Entre Métricas (Función $\psi$)

La conmutación abrupta Kerr → Alcubierre introduciría discontinuidades en las derivadas de $g_{\mu\nu}$ y, por las ecuaciones de Einstein, en $T_{\mu\nu}$. Se define un buffer de clase $C^\infty$ que gradúa la métrica efectiva en el tiempo propio $\tau$ de la Nave B.

### 5.1. Función bump estándar
Dominio $z \in \mathbb{R}$:

$$\psi(z) = \begin{cases} e^{-\frac{1}{1-z^2}} & \text{si } |z| < 1 \\ 0 & \text{si } |z| \ge 1 \end{cases}$$

Propiedades: $\psi \in C^\infty(\mathbb{R})$; $\psi$ y todas sus derivadas se anulan en $|z|=1$ (transición de clase $C^\infty$ sin salto). En el núcleo $|z|<1$, $\psi > 0$.

Variable de fase: $z(\tau) = \dfrac{2(\tau - \tau_{crit})}{\Delta\tau}$, con $\tau_{crit}$ el instante de inyección causal (coordenada temporal negativa alcanzada) y $\Delta\tau$ la ventana de mezcla.

### 5.2. Métrica efectiva

$$g_{\mu\nu}^{\text{eff}}(\tau) = \psi\bigl(z(\tau)\bigr)\, g_{\mu\nu}^{\text{Kerr}} + \Bigl[1 - \psi\bigl(z(\tau)\bigr)\Bigr]\, g_{\mu\nu}^{\text{Alcubierre}}$$

Límites:
*   $\tau \ll \tau_{crit} - \Delta\tau/2 \Rightarrow g^{\text{eff}} \approx g^{\text{Kerr}}$
*   $\tau \gg \tau_{crit} + \Delta\tau/2 \Rightarrow g^{\text{eff}} \approx g^{\text{Alcubierre}}$

*Condición de atlas:* durante la rampa se exige $\det(g_{\mu\nu}^{\text{eff}}) \neq 0$ en el chart del colector; la mezcla lineal de tensores métricos no preserva el determinante punto a punto, por lo que el lazo de control debe vigilar $\det(g^{\text{eff}})$ y el factor de forma en $Z$ en tiempo real.

### 5.3. Acoplamiento termodinámico (densidad de energía negativa)
La ignición del motor Alcubierre no es escalón; el aporte de materia exótica escala con la velocidad de mezcla:

$$\dot{\mathcal{E}}_{\text{neg}} \propto \left|\frac{d\psi}{d\tau}\right| = \left|\psi'(z)\right|\,\frac{2}{\Delta\tau}$$

El máximo de $|\dot{\mathcal{E}}_{\text{neg}}|$ ocurre cerca de $\tau = \tau_{crit}$ (centro de la bump), no en los extremos donde $\psi' \to 0$.

### 5.4. Arquitectura de control (hardware)
*   **Sincronización de fase:** Monitoreo en tiempo real del arrastre de marco ($dt\,d\phi$ de Kerr). Si el factor de forma en $Z$ fluctúa, el controlador recalibra $\Delta\tau$ o desplaza $\tau_{crit}$ vía $z(\tau)$ para mantener $|\psi'|$ acotada y evitar espaguetización.
*   **Gradiente de densidad energética:** El lazo de ignición sigue $\psi(z)$; prohibida la conmutación binaria del campo exótico.
*   **Estabilidad topológica:** Mientras $\det(g^{\text{eff}}) \neq 0$, el atlas del motor permanece válido como colector y la extracción geométrica (Fase 3) puede completarse sin ruptura del chart.

### 5.5. Coordinación de charts (implementación de referencia)
Ambas métricas se evalúan en el marco co-móvil $(t, x, y, z)$ de la Nave B en el punto de inyección $(r, \theta, \phi)$ de la ergósfera:
*   **Kerr:** Boyer–Lindquist $(t, r, \theta, \phi)$ → cartesianas locales $x = r\sin\theta\cos\phi$, $y = r\sin\theta\sin\phi$, $z = r\cos\theta$ mediante el jacobiano $J^\alpha{}_\mu$ en el punto; $g_{\alpha\beta}^{\text{cart}} = (J^{-1})^\mu{}_\alpha g_{\mu\nu}^{\text{BL}} (J^{-1})^\nu{}_\beta$.
*   **Alcubierre:** Chart co-móvil con $f(\xi)$ de Alcubierre (1994); el eje $x$ de la burbuja se rota al vector $\partial/\partial\phi$ (dirección del arrastre de marco en el ecuador) para alinear contracción/expansión con el flujo ergosférico.

*Parámetros por defecto (unidades $G=c=1$):* $r = 1{,}05\,r_+$, $\theta = \pi/2$, $a = 0{,}998\,M$, $v_s = 0{,}5$, $\sigma = 1$, $R_{\text{burbuja}} = 1$. Barrido numérico: `python metricas_motor.py` → `sweep_det_results.csv` ($\det g^{\text{eff}}$ vs $\tau$, $\Delta\tau$).

### 5.6. Lazo de control PID adaptativo (Fase 3 — materialización en firmware)
El pseudocódigo `control_transicion_metrica(z, τ)` en `control_motor.hpp` / `control_motor.py` ejecuta:
1. $\psi(z)$ con $z = 2(\tau-\tau_{crit})/\Delta\tau$.
2. $T_{\text{target}} = \psi T_{\text{Kerr}} + (1-\psi) T_{\text{Alc}}$; escala $T_{zz}$ con el factor de forma en $Z$.
3. Retroalimentación Hawking: si `radiation_leak` > `LIMITE_CRITICO`, estrechar $Z$ (`Z_COMPENSATION`) e inyectar $T_{\text{target}} - \text{compensación}$.
4. PID adaptativo sobre $\|\Delta\rho\|$ y $\|\Delta T_{zz}\|$; ganancias moduladas por $|d\psi/d\tau|$ y fuga de vacío.
5. Handover: $f_{\text{anillos}} \propto \psi$ (cierre gradual del cono de luz); $\dot m_{\text{lastre}} \propto |d\psi/d\tau|$ (Penrose, Fase 2).
6. Ruptura de emergencia: si $\det(g^{\text{eff}}) \to 0$, $|T_{zz}| \to \infty$ o $\mathrm{rank}(F_*) < 3.5$, forzar $T_{\text{Alc}}$ puro (escudo cinemático).

*Estabilidad topológica:* proxy $\mathrm{rank}(F_*) \approx 4|\det g|^{1/4}/\mathrm{tr}|g|$; la espaguetización corresponde a pérdida de rango del diferencial del mapa de handover.

Simulación: `python control_motor.py`. C++: `g++ -std=c++17 -O2 -o control_demo control_motor.cpp`.

### 5.7. Máquina de fases, $\tau_{crit}$ y presupuesto energético
*   **Fases (`fases_motor.py`):** CALIBRACION (Nave A) → DESCENSO → INYECCION_CTC (Penrose, $\dot m \propto |d\psi/d\tau|$) → RUPTURA_TOPOLOGICA (PID + $\psi$) → EXTRACCION → ABORT.
*   **$\tau_{crit}$ (`tau_crit.py`):** Se estima cuando $g_{tt}>0$ (ergósfera) y $ds^2<0$ en dirección tangente (cono cerrado / inversión temporal local).
*   **$T_{\mu\nu}$ (`einstein_proxy.py`):** Proxy linealizado $T \sim (g-\eta)/(8\pi)$ mezclado con $\psi$; condiciones WEC/NEC/SEC monitorizables.
*   **Presupuesto (`presupuesto_energia.py`):** $\eta_{\text{Penrose}}$, $E_{\text{Alc}} \sim v_s^2 R^2/(8\pi\sigma^2)$, pico de rampa vs extracción.
*   **Calibración (`calibracion.py` → `motor_config.json`):** Umbrales de det, ranking y Hawking desde el barrido CSV.
*   **Pipeline:** `python simulacion_completa.py` → `simulacion_completa.csv`. Tests: `python -m unittest tests/test_motor.py -v`.

---

## 6. Excepciones y Manejo de Errores Estructurales

*   **Excepción Hawking_Radiation_Overflow:** Si el campo de energía negativa se inestabiliza durante el cierre de la curva de tipo tiempo, la retroalimentación de las fluctuaciones del vacío destruirá la topología local.
*   **Resolución Requerida:** La geometría de inyección debe mantener el factor de forma constante; cualquier alteración en el eje ortogonal $Z$ durante el Arrastre de Marco resultará en espaguetización instantánea.
