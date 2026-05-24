"""
Visualizador de Telemetría Sci-Fi para el Motor Causal.
Usa únicamente la biblioteca estándar (Tkinter) para dibujar gráficos sin dependencias.
"""

from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "simulacion_completa.csv"


class TelemetryVisualizer:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AURA II - SSU CAUSAL TRANSIT TELEMETRY")
        self.root.geometry("1000x750")
        self.root.configure(bg="#0d0e15")

        # Leer datos
        self.data = self.read_telemetry()
        if not self.data:
            self.show_error("No se encontró 'simulacion_completa.csv'. Ejecuta primero 'python simulacion_completa.py'.")
            return

        self.setup_ui()

    def read_telemetry(self) -> list[dict] | None:
        if not CSV_FILE.is_file():
            return None
        
        data = []
        try:
            with CSV_FILE.open(encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append({
                        "tau": float(row["tau"]),
                        "fase": row["fase"],
                        "g_tt": float(row["g_tt"]),
                        "det_g": float(row["det_g"]),
                        "f_GHz": float(row["f_GHz"]),
                        "lastre": float(row["lastre"]),
                        "rho": float(row["rho"]),
                        "emergencia": row["emergencia"] == "True",
                    })
            return data
        except Exception:
            return None

    def show_error(self, message: str) -> None:
        label = tk.Label(
            self.root,
            text=message,
            fg="#ff4a4a",
            bg="#0d0e15",
            font=("Consolas", 12, "bold"),
            wraplength=800
        )
        label.pack(expand=True)

    def setup_ui(self) -> None:
        # Título estilo terminal sci-fi
        title_frame = tk.Frame(self.root, bg="#0d0e15", bd=0)
        title_frame.pack(fill=tk.X, pady=10, padx=20)

        title = tk.Label(
            title_frame,
            text="▲ AURA CAUSAL MOTOR - SIMULATION TELEMETRY",
            font=("Consolas", 16, "bold"),
            fg="#00f0ff",
            bg="#0d0e15"
        )
        title.pack(side=tk.LEFT)

        subtitle = tk.Label(
            title_frame,
            text="SYSTEM STATUS: DIAGNOSTIC ACTIVE",
            font=("Consolas", 10, "bold"),
            fg="#39ff14",
            bg="#0d0e15"
        )
        subtitle.pack(side=tk.RIGHT, pady=5)

        # Contenedor de gráficos (2x2 Grid)
        grid_frame = tk.Frame(self.root, bg="#0d0e15")
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Gráfico 1: g_tt e Inversión Temporal
        self.canvas_g_tt = self.create_plot_canvas(grid_frame, "g_tt (Curvatura Temporal)", 0, 0)
        # Gráfico 2: det(g) (Estabilidad del Chart)
        self.canvas_det = self.create_plot_canvas(grid_frame, "det(g_eff) (Volumen Métrico)", 0, 1)
        # Gráfico 3: rho (Densidad de Energía Exótica)
        self.canvas_rho = self.create_plot_canvas(grid_frame, "ρ (Densidad de Energía Exótica)", 1, 0)
        # Gráfico 4: Frecuencia de Anillos y Lastre
        self.canvas_actuators = self.create_plot_canvas(grid_frame, "Actuadores: f_anillos (Cian) y Lastre (Verde)", 1, 1)

        # Dibujar datos
        self.root.update() # Asegurar dimensiones correctas de los canvas
        self.plot_all()

    def create_plot_canvas(self, parent: tk.Frame, title: str, row: int, col: int) -> tk.Canvas:
        frame = tk.Frame(parent, bg="#141622", bd=1, relief=tk.SOLID)
        frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

        lbl = tk.Label(
            frame,
            text=title,
            font=("Consolas", 10, "bold"),
            fg="#ffffff",
            bg="#141622"
        )
        lbl.pack(anchor="w", padx=10, pady=5)

        canvas = tk.Canvas(frame, bg="#0a0b10", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        return canvas

    def plot_all(self) -> None:
        taus = [d["tau"] for d in self.data]
        min_tau, max_tau = min(taus), max(taus)

        # Plot 1: g_tt
        g_tts = [d["g_tt"] for d in self.data]
        self.draw_curve(self.canvas_g_tt, taus, g_tts, min_tau, max_tau, "#ff007f")
        # Marcar línea cero en g_tt
        self.draw_horizontal_ref(self.canvas_g_tt, g_tts, 0.0, "#555555")

        # Plot 2: det(g)
        dets = [d["det_g"] for d in self.data]
        self.draw_curve(self.canvas_det, taus, dets, min_tau, max_tau, "#bf00ff")

        # Plot 3: rho (Densidad de Energía Exótica)
        rhos = [d["rho"] for d in self.data]
        self.draw_curve(self.canvas_rho, taus, rhos, min_tau, max_tau, "#39ff14")
        self.draw_horizontal_ref(self.canvas_rho, rhos, 0.0, "#555555")

        # Plot 4: Anillos (f_GHz) y Lastre (kg/s)
        fs = [d["f_GHz"] for d in self.data]
        lastres = [d["lastre"] for d in self.data]
        
        self.draw_curve(self.canvas_actuators, taus, fs, min_tau, max_tau, "#00f0ff")
        self.draw_curve(self.canvas_actuators, taus, lastres, min_tau, max_tau, "#39ff14", secondary=True)

    def draw_horizontal_ref(self, canvas: tk.Canvas, y_data: list[float], ref_val: float, color: str) -> None:
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        min_y, max_y = min(y_data), max(y_data)
        if max_y == min_y:
            return
        
        y_pos = h - ((ref_val - min_y) / (max_y - min_y)) * h
        canvas.create_line(0, y_pos, w, y_pos, fill=color, dash=(4, 4))
        canvas.create_text(w - 30, y_pos - 10, text=f"{ref_val:.1f}", fill=color, font=("Consolas", 8))

    def draw_curve(self, canvas: tk.Canvas, x_data: list[float], y_data: list[float], min_x: float, max_x: float, color: str, secondary: bool = False) -> None:
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        min_y, max_y = min(y_data), max(y_data)
        
        # Evitar divisiones por cero
        range_x = (max_x - min_x) if max_x != min_x else 1.0
        range_y = (max_y - min_y) if max_y != min_y else 1.0

        # Dibujar cuadrícula de fondo
        if not secondary:
            for i in range(1, 5):
                grid_x = (w / 5) * i
                grid_y = (h / 5) * i
                canvas.create_line(grid_x, 0, grid_x, h, fill="#1c1d29")
                canvas.create_line(0, grid_y, w, grid_y, fill="#1c1d29")

        points = []
        for x, y in zip(x_data, y_data):
            px = ((x - min_x) / range_x) * w
            py = h - ((y - min_y) / range_y) * h
            points.append((px, py))

        # Dibujar líneas de unión
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
            
        # Dibujar puntos
        for px, py in points:
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="#ffffff")

        # Leyendas de texto en las esquinas del canvas
        if not secondary:
            canvas.create_text(15, 10, text=f"Max: {max_y:.2e}", fill="#888888", anchor="w", font=("Consolas", 8))
            canvas.create_text(15, h - 10, text=f"Min: {min_y:.2e}", fill="#888888", anchor="w", font=("Consolas", 8))
        else:
            canvas.create_text(w - 15, 10, text=f"Max2: {max_y:.2e}", fill="#888888", anchor="e", font=("Consolas", 8))
            canvas.create_text(w - 15, h - 10, text=f"Min2: {min_y:.2e}", fill="#888888", anchor="e", font=("Consolas", 8))


if __name__ == "__main__":
    app_root = tk.Tk()
    visualizer = TelemetryVisualizer(app_root)
    app_root.mainloop()
