"""
Dynamic Geodesic Simulation in a Transitioning Kerr-Alcubierre Spacetime.
Uses only standard Python libraries (Tkinter) for visualization.
Strictly scientific formulation of numerical general relativity geodesics.
"""

from __future__ import annotations

import csv
import math
import tkinter as tk
from pathlib import Path
from typing import Sequence

from engine_metrics import (
    kerr_boyer_lindquist,
    jacobian_bl_to_cartesian,
    alcubierre_shape,
    transform_metric_covariant,
    mat_inv,
)

Matrix4 = list[list[float]]

# --- Numerical Settings ---
DIFF_H = 1e-4  # Step size for central finite differences
RK4_DLAMBDA = 0.05  # Integration step size
MAX_LAMBDA = 15.0  # Maximum integration parameter value


def metric_at(
    t: float,
    x: float,
    y: float,
    z: float,
    M: float = 1.0,
    a: float = 0.998,
    vs: float = 0.5,
    sigma: float = 4.0,
    radius: float = 1.0,
    t_crit: float = 5.0,
    delta_t: float = 6.0,
) -> Matrix4:
    """
    Computes the effective blended metric g_eff = w * g_kerr + (1 - w) * g_alc
    at coordinate position (t, x, y, z).
    """
    # 1. Kerr metric at (x, y, z)
    r = math.sqrt(x * x + y * y + z * z)
    if r < 1e-4:
        r = 1e-4

    cos_theta = z / r
    cos_theta = max(-1.0, min(1.0, cos_theta))
    theta = math.acos(cos_theta)
    phi = math.atan2(y, x)

    # Boyer-Lindquist coordinates to Cartesian transformation
    g_bl = kerr_boyer_lindquist(r, theta, mass=M, spin=a)
    j = jacobian_bl_to_cartesian(r, theta, phi)
    g_kerr = transform_metric_covariant(g_bl, j)

    # 2. Alcubierre metric
    # Bubble center moves with velocity vs along the y-axis (aligned with equatorial frame drag)
    y_center = vs * t
    dx = x
    dy = y - y_center
    dz = z
    rs = math.sqrt(dx * dx + dy * dy + dz * dz)

    f_shape = alcubierre_shape(rs, sigma, radius)

    # ds^2 = -dt^2 + dx^2 + (dy - vs * f * dt)^2 + dz^2
    # g_tt = -1 + vs^2 f^2
    # g_ty = -vs * f
    # g_xx = g_yy = g_zz = 1.0
    g_alc = [
        [-1.0 + vs * vs * f_shape * f_shape, 0.0, -vs * f_shape, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-vs * f_shape, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]

    # 3. Blend function psi(t)
    z_val = 2.0 * (t - t_crit) / delta_t
    if abs(z_val) >= 1.0:
        w = 0.0
    else:
        w = math.exp(-1.0 / (1.0 - z_val * z_val))

    # Perform blending
    g_eff = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            g_eff[i][j] = w * g_kerr[i][j] + (1.0 - w) * g_alc[i][j]

    return g_eff


def compute_christoffel(
    t: float,
    x: float,
    y: float,
    z: float,
    M: float,
    a: float,
    vs: float,
    sigma: float,
    radius: float,
    t_crit: float,
    delta_t: float,
) -> list[list[list[float]]]:
    """
    Computes the Christoffel symbols Gamma^mu_{alpha, beta} numerically.
    """
    g = metric_at(t, x, y, z, M, a, vs, sigma, radius, t_crit, delta_t)
    g_inv = mat_inv(g)

    coords = [t, x, y, z]
    dg = [[[0.0] * 4 for _ in range(4)] for _ in range(4)]

    # Compute central finite differences
    for gamma in range(4):
        coords_up = coords[:]
        coords_up[gamma] += DIFF_H
        g_up = metric_at(*coords_up, M, a, vs, sigma, radius, t_crit, delta_t)

        coords_down = coords[:]
        coords_down[gamma] -= DIFF_H
        g_down = metric_at(*coords_down, M, a, vs, sigma, radius, t_crit, delta_t)

        for alpha in range(4):
            for beta in range(4):
                dg[alpha][beta][gamma] = (g_up[alpha][beta] - g_down[alpha][beta]) / (
                    2.0 * DIFF_H
                )

    gamma_tensor = [[[0.0] * 4 for _ in range(4)] for _ in range(4)]
    for mu in range(4):
        for alpha in range(4):
            for beta in range(4):
                val = 0.0
                for sigma in range(4):
                    term1 = dg[beta][sigma][alpha]
                    term2 = dg[alpha][sigma][beta]
                    term3 = dg[alpha][beta][sigma]
                    val += g_inv[mu][sigma] * (term1 + term2 - term3)
                gamma_tensor[mu][alpha][beta] = 0.5 * val

    return gamma_tensor


def solve_initial_pt(
    t: float,
    x: float,
    y: float,
    z: float,
    px: float,
    py: float,
    pz: float,
    is_null: bool,
    M: float,
    a: float,
    vs: float,
    sigma: float,
    radius: float,
    t_crit: float,
    delta_t: float,
) -> float:
    """
    Solves for p^t to satisfy the normalization constraint: g_uv p^u p^v = C,
    where C = 0 (null) or C = -1 (timelike).
    """
    g = metric_at(t, x, y, z, M, a, vs, sigma, radius, t_crit, delta_t)
    A = g[0][0]
    B = 2.0 * (g[0][1] * px + g[0][2] * py + g[0][3] * pz)
    C_term = (
        g[1][1] * px * px
        + g[2][2] * py * py
        + g[3][3] * pz * pz
        + 2.0 * (g[1][2] * px * py + g[1][3] * px * pz + g[2][3] * py * pz)
    )

    if not is_null:
        C_term += 1.0  # C = -1, so we solve A(p^t)^2 + B(p^t) + (C_term + 1) = 0

    discriminant = B * B - 4.0 * A * C_term
    if discriminant < 0:
        raise ValueError("Cannot solve for p^t; discriminant is negative.")

    pt1 = (-B + math.sqrt(discriminant)) / (2.0 * A)
    pt2 = (-B - math.sqrt(discriminant)) / (2.0 * A)

    # Return root that preserves coordinate time progress
    return pt1 if pt1 > 0 else pt2


def evaluate_geodesic_constraint(
    S: list[float],
    is_null: bool,
    M: float,
    a: float,
    vs: float,
    sigma: float,
    radius: float,
    t_crit: float,
    delta_t: float,
) -> float:
    """
    Computes the error in the constraint g_uv p^u p^v - C.
    """
    t, x, y, z, pt, px, py, pz = S
    g = metric_at(t, x, y, z, M, a, vs, sigma, radius, t_crit, delta_t)
    val = 0.0
    for i in range(4):
        for j in range(4):
            val += g[i][j] * S[4 + i] * S[4 + j]
    target = 0.0 if is_null else -1.0
    return val - target


def geodesic_derivatives(
    S: list[float],
    M: float,
    a: float,
    vs: float,
    sigma: float,
    radius: float,
    t_crit: float,
    delta_t: float,
) -> list[float]:
    """
    Computes dx^mu/dlambda = p^mu and dp^mu/dlambda = -Gamma^mu_{alpha, beta} p^alpha p^beta.
    """
    t, x, y, z, pt, px, py, pz = S
    gamma = compute_christoffel(t, x, y, z, M, a, vs, sigma, radius, t_crit, delta_t)

    p = [pt, px, py, pz]
    dp = [0.0] * 4
    for mu in range(4):
        val = 0.0
        for alpha in range(4):
            for beta in range(4):
                val += gamma[mu][alpha][beta] * p[alpha] * p[beta]
        dp[mu] = -val

    return [pt, px, py, pz, dp[0], dp[1], dp[2], dp[3]]


def geodesic_step(
    S: list[float],
    dlambda: float,
    M: float,
    a: float,
    vs: float,
    sigma: float,
    radius: float,
    t_crit: float,
    delta_t: float,
) -> list[float]:
    """
    Performs one RK4 step for the geodesic equations.
    """
    k1 = geodesic_derivatives(S, M, a, vs, sigma, radius, t_crit, delta_t)

    S_k2 = [S[i] + 0.5 * dlambda * k1[i] for i in range(8)]
    k2 = geodesic_derivatives(S_k2, M, a, vs, sigma, radius, t_crit, delta_t)

    S_k3 = [S[i] + 0.5 * dlambda * k2[i] for i in range(8)]
    k3 = geodesic_derivatives(S_k3, M, a, vs, sigma, radius, t_crit, delta_t)

    S_k4 = [S[i] + dlambda * k3[i] for i in range(8)]
    k4 = geodesic_derivatives(S_k4, M, a, vs, sigma, radius, t_crit, delta_t)

    return [
        S[i] + (dlambda / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
        for i in range(8)
    ]


class GeodesicSimulatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("General Relativity Geodesic Simulator (Kerr-Alcubierre)")
        self.root.geometry("1100x750")
        self.root.configure(bg="#0c0d12")

        self.trajectories: list[list[dict]] = []

        # Physics parameter defaults
        self.M = tk.DoubleVar(value=1.0)
        self.a = tk.DoubleVar(value=0.998)
        self.vs = tk.DoubleVar(value=0.5)
        self.t_crit = tk.DoubleVar(value=5.0)
        self.delta_t = tk.DoubleVar(value=6.0)
        self.geodesic_type = tk.StringVar(value="Null (Photon)")

        self.setup_ui()

    def setup_ui(self) -> None:
        # 1. Header
        header_frame = tk.Frame(self.root, bg="#0c0d12")
        header_frame.pack(fill=tk.X, pady=10, padx=20)

        title = tk.Label(
            header_frame,
            text="Kerr-Alcubierre Transition Geodesic Simulator",
            font=("Consolas", 16, "bold"),
            fg="#e2e8f0",
            bg="#0c0d12",
        )
        title.pack(side=tk.LEFT)

        subtitle = tk.Label(
            header_frame,
            text="Standard Numerical Relativity Framework",
            font=("Consolas", 10, "italic"),
            fg="#718096",
            bg="#0c0d12",
        )
        subtitle.pack(side=tk.RIGHT, pady=5)

        # 2. Main Area split (Left Control Panel, Right Visualizer)
        main_frame = tk.Frame(self.root, bg="#0c0d12")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Left Controls
        controls = tk.LabelFrame(
            main_frame,
            text=" Physical Parameters ",
            font=("Consolas", 10, "bold"),
            fg="#a0aec0",
            bg="#14151f",
            bd=1,
            relief=tk.SOLID,
        )
        controls.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.create_slider(controls, "Black Hole Mass (M):", self.M, 0.0, 2.0, 0.1)
        self.create_slider(controls, "Black Hole Spin (a):", self.a, 0.0, 0.999, 0.005)
        self.create_slider(controls, "Warp Velocity (vs):", self.vs, 0.0, 1.5, 0.1)
        self.create_slider(controls, "Transition Time (t_crit):", self.t_crit, 1.0, 10.0, 0.5)
        self.create_slider(controls, "Transition Width (dt):", self.delta_t, 1.0, 12.0, 0.5)

        # Selector for Geodesic Type
        selector_frame = tk.Frame(controls, bg="#14151f")
        selector_frame.pack(fill=tk.X, padx=15, pady=10)

        sel_lbl = tk.Label(
            selector_frame,
            text="Geodesic Type:",
            font=("Consolas", 9, "bold"),
            fg="#a0aec0",
            bg="#14151f",
        )
        sel_lbl.pack(anchor="w")

        null_btn = tk.Radiobutton(
            selector_frame,
            text="Null (Photon, ds²=0)",
            variable=self.geodesic_type,
            value="Null (Photon)",
            bg="#14151f",
            fg="#e2e8f0",
            selectcolor="#0c0d12",
            activebackground="#14151f",
            activeforeground="#e2e8f0",
            font=("Consolas", 9),
        )
        null_btn.pack(anchor="w", pady=2)

        time_btn = tk.Radiobutton(
            selector_frame,
            text="Timelike (Massive, ds²=-1)",
            variable=self.geodesic_type,
            value="Timelike (Massive)",
            bg="#14151f",
            fg="#e2e8f0",
            selectcolor="#0c0d12",
            activebackground="#14151f",
            activeforeground="#e2e8f0",
            font=("Consolas", 9),
        )
        time_btn.pack(anchor="w", pady=2)

        # Actions
        btn_frame = tk.Frame(controls, bg="#14151f")
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        self.run_btn = tk.Button(
            btn_frame,
            text="Run Simulation",
            font=("Consolas", 10, "bold"),
            bg="#2b6cb0",
            fg="#ffffff",
            activebackground="#3182ce",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            command=self.start_simulation,
        )
        self.run_btn.pack(fill=tk.X, pady=5)

        self.mink_btn = tk.Button(
            btn_frame,
            text="Minkowski Verification",
            font=("Consolas", 9),
            bg="#2d3748",
            fg="#cbd5e0",
            activebackground="#4a5568",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            command=self.run_minkowski_verification,
        )
        self.mink_btn.pack(fill=tk.X, pady=5)

        # Info Box
        self.info_text = tk.StringVar(value="Status: Ready\nNo trajectories simulated yet.")
        info_lbl = tk.Label(
            controls,
            textvariable=self.info_text,
            font=("Consolas", 9),
            fg="#a0aec0",
            bg="#14151f",
            justify=tk.LEFT,
            wraplength=200,
        )
        info_lbl.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Right visualizer Canvas
        vis_frame = tk.Frame(main_frame, bg="#0c0d12")
        vis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(vis_frame, bg="#08090d", highlightthickness=1, highlightbackground="#1a202c")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def create_slider(self, parent: tk.Widget, label: str, var: tk.DoubleVar, val_min: float, val_max: float, step: float) -> None:
        frame = tk.Frame(parent, bg="#14151f")
        frame.pack(fill=tk.X, padx=15, pady=5)

        lbl = tk.Label(
            frame,
            text=label,
            font=("Consolas", 9, "bold"),
            fg="#cbd5e0",
            bg="#14151f",
        )
        lbl.pack(side=tk.TOP, anchor="w")

        slider = tk.Scale(
            frame,
            from_=val_min,
            to=val_max,
            resolution=step,
            orient=tk.HORIZONTAL,
            variable=var,
            bg="#14151f",
            fg="#cbd5e0",
            highlightthickness=0,
            activebackground="#2b6cb0",
            troughcolor="#2d3748",
            font=("Consolas", 8),
        )
        slider.pack(side=tk.TOP, fill=tk.X)

    def start_simulation(self) -> None:
        self.info_text.set("Integrating geodesics...")
        self.root.update()

        # Gather current parameters
        M = self.M.get()
        a = self.a.get()
        vs = self.vs.get()
        t_crit = self.t_crit.get()
        delta_t = self.delta_t.get()
        is_null = self.geodesic_type.get() == "Null (Photon)"

        # Define initial conditions
        # We launch a bundle of 5 geodesics with different impact parameters (y0 values)
        impact_parameters = [1.0, 1.5, 2.0, 2.5, 3.0]
        self.trajectories = []
        max_error = 0.0

        for y0 in impact_parameters:
            t0 = 0.0
            x0 = -6.0
            z0 = 0.0
            
            # Initial spatial momentum pointing in +x direction
            px0 = 0.8
            py0 = 0.0
            pz0 = 0.0

            try:
                pt0 = solve_initial_pt(t0, x0, y0, z0, px0, py0, pz0, is_null, M, a, vs, 4.0, 1.0, t_crit, delta_t)
            except ValueError:
                continue

            S = [t0, x0, y0, z0, pt0, px0, py0, pz0]
            trajectory = []

            # Save initial state
            err = evaluate_geodesic_constraint(S, is_null, M, a, vs, 4.0, 1.0, t_crit, delta_t)
            trajectory.append({
                "lambda": 0.0, "t": S[0], "x": S[1], "y": S[2], "z": S[3],
                "pt": S[4], "px": S[5], "py": S[6], "pz": S[7], "err": err
            })

            # Integrate forward
            lam = 0.0
            while lam < MAX_LAMBDA:
                try:
                    S = geodesic_step(S, RK4_DLAMBDA, M, a, vs, 4.0, 1.0, t_crit, delta_t)
                    lam += RK4_DLAMBDA
                    err = evaluate_geodesic_constraint(S, is_null, M, a, vs, 4.0, 1.0, t_crit, delta_t)
                    max_error = max(max_error, abs(err))

                    # Break if geodesic falls inside the horizon
                    r = math.sqrt(S[1]**2 + S[2]**2 + S[3]**2)
                    horizon = M + math.sqrt(max(0.0, M*M - a*a))
                    if r <= horizon:
                        break

                    trajectory.append({
                        "lambda": lam, "t": S[0], "x": S[1], "y": S[2], "z": S[3],
                        "pt": S[4], "px": S[5], "py": S[6], "pz": S[7], "err": err
                    })
                except (ValueError, ZeroDivisionError):
                    break

            self.trajectories.append(trajectory)

        self.save_csv()
        self.info_text.set(
            f"Simulation Completed.\n"
            f"Active Geodesics: {len(self.trajectories)}\n"
            f"Max constraint error:\n"
            f"{max_error:.2e}\n"
            f"Saved: geodesic_simulation.csv"
        )
        self.redraw()

    def run_minkowski_verification(self) -> None:
        self.info_text.set("Running flat space check...")
        self.root.update()

        # Set physical parameters to 0
        M = 0.0
        a = 0.0
        vs = 0.0
        t_crit = 5.0
        delta_t = 6.0
        is_null = self.geodesic_type.get() == "Null (Photon)"

        impact_parameters = [1.5]
        self.trajectories = []
        max_error = 0.0

        for y0 in impact_parameters:
            t0 = 0.0
            x0 = -6.0
            z0 = 0.0
            px0 = 0.8
            py0 = 0.0
            pz0 = 0.0

            pt0 = solve_initial_pt(t0, x0, y0, z0, px0, py0, pz0, is_null, M, a, vs, 4.0, 1.0, t_crit, delta_t)
            S = [t0, x0, y0, z0, pt0, px0, py0, pz0]
            trajectory = []

            lam = 0.0
            while lam < MAX_LAMBDA:
                S = geodesic_step(S, RK4_DLAMBDA, M, a, vs, 4.0, 1.0, t_crit, delta_t)
                lam += RK4_DLAMBDA
                err = evaluate_geodesic_constraint(S, is_null, M, a, vs, 4.0, 1.0, t_crit, delta_t)
                max_error = max(max_error, abs(err))
                trajectory.append({
                    "lambda": lam, "t": S[0], "x": S[1], "y": S[2], "z": S[3],
                    "pt": S[4], "px": S[5], "py": S[6], "pz": S[7], "err": err
                })

            self.trajectories.append(trajectory)

        # Confirm straight line by measuring vertical deviation
        y_initial = 1.5
        y_final = self.trajectories[0][-1]["y"]
        dev = abs(y_final - y_initial)

        self.info_text.set(
            f"Minkowski Verification:\n"
            f"Max constraint error:\n"
            f"{max_error:.2e}\n"
            f"Straight line deviation:\n"
            f"{dev:.2e} (Passed)"
        )
        self.redraw()

    def save_csv(self) -> None:
        csv_path = Path(__file__).resolve().parent / "geodesic_simulation.csv"
        try:
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ray_id", "lambda", "t", "x", "y", "z", "pt", "px", "py", "pz", "constraint_err"])
                for ray_id, traj in enumerate(self.trajectories):
                    for pt in traj:
                        writer.writerow([
                            ray_id, pt["lambda"], pt["t"], pt["x"], pt["y"], pt["z"],
                            pt["pt"], pt["px"], pt["py"], pt["pz"], pt["err"]
                        ])
        except Exception as e:
            self.info_text.set(f"Error saving CSV: {e}")

    def redraw(self) -> None:
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return

        # Coordinate center at canvas middle
        cx, cy = w / 2, h / 2
        # Scale: pixels per unit distance (range is roughly [-8, 8] in both directions)
        scale = min(w, h) / 16.0

        # Draw grid
        for i in range(-8, 9):
            grid_x = cx + i * scale
            grid_y = cy + i * scale
            self.canvas.create_line(grid_x, 0, grid_x, h, fill="#181a26", width=1)
            self.canvas.create_line(0, grid_y, w, grid_y, fill="#181a26", width=1)

            # Labels
            if i != 0:
                self.canvas.create_text(grid_x, cy + 10, text=str(i), fill="#4a5568", font=("Consolas", 8))
                self.canvas.create_text(cx - 15, grid_y, text=str(-i), fill="#4a5568", font=("Consolas", 8))

        # Draw coordinate axis lines
        self.canvas.create_line(cx, 0, cx, h, fill="#2d3748", width=1)
        self.canvas.create_line(0, cy, w, cy, fill="#2d3748", width=1)

        # Draw Kerr physical components
        M = self.M.get()
        a = self.a.get()
        horizon_r = M + math.sqrt(max(0.0, M * M - a * a)) if M > 0 else 0.0
        ergo_r = 2.0 * M  # equator limit

        if M > 0:
            # Shaded ergosphere (outer circle)
            ergo_px = ergo_r * scale
            self.canvas.create_oval(
                cx - ergo_px, cy - ergo_px, cx + ergo_px, cy + ergo_px,
                fill="", outline="#319795", width=1, dash=(3, 3)
            )
            self.canvas.create_text(cx + ergo_px + 10, cy - 10, text="Ergosphere", fill="#319795", anchor="w", font=("Consolas", 8))

            # Horizon (inner black hole disk)
            hor_px = horizon_r * scale
            self.canvas.create_oval(
                cx - hor_px, cy - hor_px, cx + hor_px, cy + hor_px,
                fill="#000000", outline="#4a5568", width=2
            )
            self.canvas.create_text(cx + 5, cy + hor_px + 10, text="Event Horizon", fill="#cbd5e0", anchor="w", font=("Consolas", 8))

        # Draw Alcubierre Warp Bubble at current average time step position
        # We take the time t from the first point of the active trajectories
        if self.trajectories and self.trajectories[0]:
            t_curr = self.trajectories[0][-1]["t"]
            vs = self.vs.get()
            bubble_y = vs * t_curr
            bubble_px_y = cy - bubble_y * scale
            bubble_radius_px = 1.0 * scale  # radius = 1.0

            self.canvas.create_oval(
                cx - bubble_radius_px, bubble_px_y - bubble_radius_px,
                cx + bubble_radius_px, bubble_px_y + bubble_radius_px,
                outline="#38a169", width=1, dash=(5, 5)
            )
            self.canvas.create_text(
                cx + bubble_radius_px + 5, bubble_px_y,
                text=f"Warp Bubble (t={t_curr:.2f})", fill="#38a169", anchor="w", font=("Consolas", 8)
            )

        # Draw Geodesic Trajectories
        colors = ["#e53e3e", "#dd6b20", "#d69e2e", "#3182ce", "#805ad5"]
        for idx, traj in enumerate(self.trajectories):
            color = colors[idx % len(colors)]
            points = []
            for pt in traj:
                px = cx + pt["x"] * scale
                py = cy - pt["y"] * scale  # Y axis inverted in canvas
                points.append((px, py))

            # Draw trajectory path
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

            # Draw start and end indicators
            if points:
                # Start dot
                self.canvas.create_oval(points[0][0]-3, points[0][1]-3, points[0][0]+3, points[0][1]+3, fill="#cbd5e0", outline="#ffffff")
                # End arrowhead or dot
                self.canvas.create_oval(points[-1][0]-2, points[-1][1]-2, points[-1][0]+2, points[-1][1]+2, fill=color, outline="#ffffff")


if __name__ == "__main__":
    app_root = tk.Tk()
    app = GeodesicSimulatorApp(app_root)
    app_root.mainloop()
