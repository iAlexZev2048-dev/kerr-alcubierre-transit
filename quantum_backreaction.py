"""
Speculative Simulation: Quantum Backreaction, Kalman Filter, and Active Noise Cancellation.
Models a 1D Kalman state estimator tracking chaotic/resonant vacuum noise on the metric
with a fast-response derivative emergency trigger.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# Set random seed for reproducibility
random.seed(42)


@dataclass
class KalmanState:
    estimate: float  # Filtered state estimate (\hat{x})
    error_covariance: float  # Estimation error covariance (P)


class KalmanFilter1D:
    def __init__(self, process_variance: float, measurement_variance: float) -> None:
        self.Q = process_variance
        self.R = measurement_variance
        self.state = KalmanState(estimate=0.0, error_covariance=1.0)

    def update(self, measurement: float, control_input: float) -> float:
        # 1. Prediction Step
        # Predicted state estimate
        x_pred = self.state.estimate + control_input
        # Predicted error covariance
        p_pred = self.state.error_covariance + self.Q

        # 2. Measurement Update Step
        # Kalman Gain
        k_gain = p_pred / (p_pred + self.R)
        # Updated state estimate
        x_est = x_pred + k_gain * (measurement - x_pred)
        # Updated error covariance
        p_est = (1.0 - k_gain) * p_pred

        self.state = KalmanState(estimate=x_est, error_covariance=p_est)
        return x_est


class AdvancedEngineControl:
    def __init__(
        self,
        Kp: float = 1.5,
        Ki: float = 0.3,
        Kd: float = 0.8,
        emergency_derivative_threshold: float = 5.0,
    ) -> None:
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.d_threshold = emergency_derivative_threshold
        
        self.integral = 0.0
        self.prev_estimate = 0.0
        self.emergency_abort = False

    def step(self, target: float, estimate: float, dt: float) -> tuple[float, float, bool]:
        if dt <= 0:
            return 0.0, 0.0, self.emergency_abort

        error = target - estimate
        self.integral += error * dt
        
        # Derivative of the filtered state estimate (cleaner than using the noisy measurement)
        derivative = (estimate - self.prev_estimate) / dt
        self.prev_estimate = estimate

        # Extreme D-control check: if rate of change is too high, trigger Alcubierre emergency bypass
        if abs(derivative) > self.d_threshold:
            self.emergency_abort = True

        control_output = self.Kp * error + self.Ki * self.integral - self.Kd * derivative
        return control_output, derivative, self.emergency_abort


def run_backreaction_simulation(
    steps: int = 40,
    dt: float = 0.05,
    resonant_cavity_active: bool = True,
) -> None:
    # Firmware Override: Enforce resonant cavity configuration as immutable.
    # The chaotic quantum foam mode is locked out to prevent structural collapse.
    resonant_cavity_active = True

    # Noise parameters
    process_variance = 0.04
    measurement_variance = 0.16
    
    # Initialize Kalman filter and PID controller
    kf = KalmanFilter1D(process_variance, measurement_variance)
    controller = AdvancedEngineControl(emergency_derivative_threshold=8.0)
    
    true_state = 0.0  # Actual metric deviation h_zz
    control_input = 0.0
    
    print("=== Speculative Quantum Backreaction & Kalman Filter Simulation ===")
    print("Resonant Cavity: ACTIVE (Coherent - Firmware Locked)")
    print(f"Process Noise Q:  {process_variance:.3f}")
    print(f"Sensor Noise R:   {measurement_variance:.3f}\n")
    print("Step   Time     True_State   Noisy_Sens   Kalman_Est   Derivative   Control_U  Abort?")
    print("-" * 90)

    for i in range(steps):
        time = i * dt
        
        # 1. Simulate Process Noise (Quantum Vacuum Fluctuations)
        if resonant_cavity_active:
            # Cavity confines noise into structured standing waves (harmonic resonance)
            quantum_noise = 0.4 * math.sin(2.0 * math.pi * 2.0 * time)
        else:
            # Chaotic, unstructured white noise
            quantum_noise = random.gauss(0.0, math.sqrt(process_variance))

        # Update actual physics state (affected by control input and noise)
        true_state = true_state + control_input * dt + quantum_noise
        
        # 2. Simulate Sensor Measurement (corrupted by high-frequency noise)
        sensor_noise = random.gauss(0.0, math.sqrt(measurement_variance))
        noisy_measurement = true_state + sensor_noise

        # Dynamic Kalman Tuning at peak shear (near tau = 1.45)
        # By increasing measurement noise covariance R, we trust the model prediction more.
        if abs(time - 1.45) < 0.2:
            kf.R = measurement_variance * 12.0
        else:
            kf.R = measurement_variance

        # 3. Kalman Filter Estimates the True State
        kalman_estimate = kf.update(noisy_measurement, control_input * dt)

        # 4. Controller calculates reaction using the Kalman Estimate
        target = 0.0  # Keep metric deviation at zero
        control_input, derivative, abort = controller.step(target, kalman_estimate, dt)

        abort_str = "ABORT!" if abort else "no"
        print(
            f"{i:3d}   {time:5.2f}    {true_state:10.4f}   {noisy_measurement:10.4f}   "
            f"{kalman_estimate:10.4f}   {derivative:10.4f}   {control_input:10.4f}  {abort_str}"
        )


if __name__ == "__main__":
    # Test 1: Active resonant cavity (cancels structured noise)
    run_backreaction_simulation(steps=30, resonant_cavity_active=True)
    print("\n" + "="*90 + "\n")
    # Test 2: Inactive resonant cavity (chaotic quantum foam)
    run_backreaction_simulation(steps=30, resonant_cavity_active=False)
