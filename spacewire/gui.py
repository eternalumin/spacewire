"""Modern Tkinter GUI for SpaceWire/SpaceFibre network simulation."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import random
from typing import Optional, Dict, List, Any
from collections import deque

from spacewire.topology import (
    TopologyBuilder, TopologyType, Topology, 
    get_topology, format_node_id
)
from spacewire.packet import SpaceWirePacket, SpaceFibrePacket, PacketPriority
from spacewire.metrics import MetricsCollector, QoSMetrics
from spacewire.config import Config, get_config
from spacewire.logging_config import setup_logging, get_logger


COLORS = {
    "background": "#1E1E2E",
    "surface": "#2D2D3F",
    "primary": "#7C3AED",
    "secondary": "#06B6D4",
    "success": "#10B981",
    "error": "#EF4444",
    "warning": "#F59E0B",
    "text": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "border": "#3F3F5A",
}

NODE_COLORS = {
    0x01: "#EF4444",  # Red - OBC
    0x02: "#F59E0B",  # Orange - Router
    0x03: "#10B981",  # Green - Camera
    0x04: "#3B82F6",  # Blue - SSD
    0x05: "#8B5CF6",  # Purple - AOCS
}

NODE_IMAGES = {
    0x01: "💻",  # OBC
    0x02: "🔀",  # Router
    0x03: "📷",  # Camera
    0x04: "💾",  # SSD
    0x05: "🛰️",  # AOCS
}


class NetworkCanvas(tk.Canvas):
    """Custom canvas for network topology visualization."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.nodes: Dict[int, tuple] = {}
        self.edges: List[tuple] = []
        self.node_labels: Dict[int, int] = {}
        self.packet_anim = None

    def draw_topology(self, topology: Topology, canvas_width: int, canvas_height: int) -> None:
        """Draw network topology."""
        self.delete("all")
        self.nodes.clear()
        self.edges.clear()
        self.node_labels.clear()

        node_list = list(topology.nodes.values())
        if not node_list:
            return

        center_x, center_y = canvas_width // 2, canvas_height // 2
        radius = min(canvas_width, canvas_height) // 3

        for i, node in enumerate(node_list):
            angle = (2 * 3.14159 * i) / len(node_list) - 3.14159 / 2
            x = center_x + radius * (1 if len(node_list) == 1 else 0.5) * (1 + 0.5 * (i % 2)) * (1 if i % 2 == 0 else -0.3) * (1 if i < len(node_list) // 2 else -1) * 0.7 * (i % 3 + 1)
            y = center_y + radius * (i / len(node_list) - 0.5) * 1.5

            positions = {
                0x01: (150, 300),
                0x02: (350, 100),
                0x03: (550, 100),
                0x04: (350, 500),
                0x05: (550, 500),
            }
            x, y = positions.get(node.id, (x, y))

            self.nodes[node.id] = (x, y)

        for src, dsts in topology.edges.items():
            if src not in self.nodes:
                continue
            for dst in dsts:
                if dst in self.nodes:
                    self.create_line(
                        self.nodes[src][0], self.nodes[src][1],
                        self.nodes[dst][0], self.nodes[dst][1],
                        fill=COLORS["border"], width=2
                    )

        for node_id, (x, y) in self.nodes.items():
            color = NODE_COLORS.get(node_id, COLORS["primary"])
            emoji = NODE_IMAGES.get(node_id, "📡")

            self.create_oval(
                x - 30, y - 30, x + 30, y + 30,
                fill=color, outline=COLORS["border"], width=2
            )

            label_id = self.create_text(
                x, y, text=emoji, font=("Segoe UI Emoji", 20),
                fill=COLORS["text"]
            )
            self.node_labels[node_id] = label_id

            self.create_text(
                x, y + 45, text=f"0x{node_id:02X}",
                font=("Consolas", 10), fill=COLORS["text_secondary"]
            )

    def animate_packet(self, path: List[int], callback=None) -> None:
        """Animate packet along path."""
        if len(path) < 2:
            return

        positions = [self.nodes[node_id] for node_id in path if node_id in self.nodes]
        if len(positions) < 2:
            return

        packet = self.create_oval(
            positions[0][0] - 8, positions[0][1] - 8,
            positions[0][0] + 8, positions[0][1] + 8,
            fill=COLORS["success"], outline=COLORS["text"]
        )

        def animate_step(index=0):
            if index >= len(positions) - 1:
                self.delete(packet)
                if callback:
                    callback()
                return

            x1, y1 = positions[index]
            x2, y2 = positions[index + 1]
            steps = 20

            def move_step(step=0):
                if step >= steps:
                    animate_step(index + 1)
                    return

                t = step / steps
                x = (1 - t) * x1 + t * x2
                y = (1 - t) * y1 + t * y2
                self.coords(packet, x - 8, y - 8, x + 8, y + 8)
                self.after(20, lambda: move_step(step + 1))

            move_step()

        animate_step()


class SpaceWireGUI:
    """Main GUI application for SpaceWire simulation."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SpaceWire/SpaceFibre Network Simulator")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["background"])

        self.config = get_config()
        self.metrics = MetricsCollector()
        self.qos_metrics = QoSMetrics()
        self.simulation_running = False
        self.simulation_thread: Optional[threading.Thread] = None
        self.current_topology: Optional[Topology] = None
        self.log_messages = deque(maxlen=1000)

        self._setup_styles()
        self._create_widgets()
        self._create_menu()
        self._load_default_topology()

        setup_logging(level=20)
        self.logger = get_logger("gui")

    def _setup_styles(self) -> None:
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=COLORS["background"])
        style.configure("Card.TFrame", background=COLORS["surface"], relief="flat")
        style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=COLORS["text"])
        style.configure("Subtitle.TLabel", font=("Segoe UI", 12), foreground=COLORS["text_secondary"])
        style.configure("TButton", font=("Segoe UI", 11), padding=10)
        style.configure("Primary.TButton", background=COLORS["primary"], foreground=COLORS["text"])
        style.configure("Success.TButton", background=COLORS["success"], foreground=COLORS["text"])
        style.configure("Danger.TButton", background=COLORS["error"], foreground=COLORS["text"])
        style.configure("TCombobox", fieldbackground=COLORS["surface"], background=COLORS["primary"])

        style.map("TButton", background=[("active", COLORS["secondary"])])
        style.map("Primary.TButton", background=[("active", COLORS["secondary"])])

    def _create_widgets(self) -> None:
        """Create GUI widgets."""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="🛰️ SpaceWire/SpaceFibre Network Simulator",
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)

        self.status_label = ttk.Label(
            header_frame,
            text="● Ready",
            foreground=COLORS["success"],
            font=("Segoe UI", 11)
        )
        self.status_label.pack(side=tk.RIGHT)

        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(content_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        self._create_control_panel(left_panel)
        self._create_metrics_panel(left_panel)

        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._create_topology_canvas(right_panel)
        self._create_log_panel(right_panel)

    def _create_control_panel(self, parent: ttk.Frame) -> None:
        """Create control panel widgets."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(card, text="⚙️ Configuration", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(card, text="Topology:").pack(anchor=tk.W)
        self.topology_var = tk.StringVar(value="point-to-point")
        topology_combo = ttk.Combobox(
            card, textvariable=self.topology_var,
            values=["star", "ring", "mesh", "tree", "point-to-point", "bus"],
            state="readonly", font=("Consolas", 10)
        )
        topology_combo.pack(fill=tk.X, pady=(0, 10))
        topology_combo.bind("<<ComboboxSelected>>", lambda e: self._on_topology_change())

        ttk.Label(card, text="Source Node:").pack(anchor=tk.W)
        self.src_var = tk.StringVar(value="0x01")
        src_combo = ttk.Combobox(
            card, textvariable=self.src_var,
            values=["0x01", "0x02", "0x03", "0x04", "0x05"],
            state="readonly", font=("Consolas", 10)
        )
        src_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(card, text="Destination Node:").pack(anchor=tk.W)
        self.dst_var = tk.StringVar(value="0x03")
        dst_combo = ttk.Combobox(
            card, textvariable=self.dst_var,
            values=["0x01", "0x02", "0x03", "0x04", "0x05"],
            state="readonly", font=("Consolas", 10)
        )
        dst_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(card, text="Protocol:").pack(anchor=tk.W)
        self.protocol_var = tk.StringVar(value="SpaceWire")
        protocol_combo = ttk.Combobox(
            card, textvariable=self.protocol_var,
            values=["SpaceWire", "SpaceFibre"],
            state="readonly", font=("Consolas", 10)
        )
        protocol_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(card, text="Error Rate (%):").pack(anchor=tk.W)
        self.error_rate_var = tk.StringVar(value="10")
        error_rate_entry = ttk.Entry(card, textvariable=self.error_rate_var, font=("Consolas", 10))
        error_rate_entry.pack(fill=tk.X, pady=(0, 15))

        button_frame = ttk.Frame(card)
        button_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            button_frame, text="▶ Start Simulation",
            style="Success.TButton", command=self._start_simulation
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.stop_btn = ttk.Button(
            button_frame, text="⏹ Stop",
            style="Danger.TButton", command=self._stop_simulation, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            card, text="📁 Load File",
            command=self._load_file
        ).pack(fill=tk.X, pady=(10, 0))

    def _create_metrics_panel(self, parent: ttk.Frame) -> None:
        """Create metrics display panel."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card, text="📊 Live Metrics", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))

        metrics_frame = ttk.Frame(card)
        metrics_frame.pack(fill=tk.BOTH, expand=True)

        self.metric_labels = {}
        metrics = [
            ("Packets Sent", "packets_sent"),
            ("Packets Received", "packets_received"),
            ("Errors Detected", "errors_detected"),
            ("Error Rate", "error_rate"),
            ("Avg Latency", "avg_latency"),
            ("Throughput", "throughput"),
            ("Power (mW)", "power"),
        ]

        for i, (label, key) in enumerate(metrics):
            row, col = i // 2, (i % 2) * 2
            
            metric_label = ttk.Label(
                metrics_frame,
                text=f"{label}:",
                font=("Consolas", 10, "bold"),
                foreground=COLORS["text_secondary"]
            )
            metric_label.grid(row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5)

            value_label = ttk.Label(
                metrics_frame,
                text="0",
                font=("Consolas", 10),
                foreground=COLORS["secondary"]
            )
            value_label.grid(row=row, column=col + 1, sticky=tk.W, pady=5)
            self.metric_labels[key] = value_label

        self.progress = ttk.Progressbar(
            card, mode="indeterminate", length=200
        )

    def _create_topology_canvas(self, parent: ttk.Frame) -> None:
        """Create topology visualization canvas."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=10)
        card.pack(fill=tk.BOTH, expand=True, padx=(0, 0), pady=(0, 10))

        ttk.Label(card, text="🕸️ Network Topology", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))

        self.canvas = NetworkCanvas(card, bg=COLORS["surface"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _create_log_panel(self, parent: ttk.Frame) -> None:
        """Create log panel."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=10)
        card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card, text="📋 Event Log", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(
            card, height=8, bg=COLORS["surface"],
            fg=COLORS["text"], font=("Consolas", 9),
            relief=tk.FLAT, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Configuration", command=self._load_config)
        file_menu.add_command(label="Save Configuration", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Metrics", command=self._export_metrics)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        simulation_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=simulation_menu)
        simulation_menu.add_command(label="Start", command=self._start_simulation)
        simulation_menu.add_command(label="Stop", command=self._stop_simulation)
        simulation_menu.add_command(label="Reset", command=self._reset_metrics)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _load_default_topology(self) -> None:
        """Load default topology."""
        self._on_topology_change()

    def _on_topology_change(self) -> None:
        """Handle topology change."""
        topo_name = self.topology_var.get()
        src = int(self.src_var.get(), 16)
        dst = int(self.dst_var.get(), 16)

        builders = {
            "star": TopologyBuilder.star,
            "ring": TopologyBuilder.ring,
            "mesh": TopologyBuilder.mesh,
            "tree": TopologyBuilder.tree,
            "point-to-point": TopologyBuilder.point_to_point,
            "bus": TopologyBuilder.bus,
        }

        devices = [0x01, 0x02, 0x03, 0x04, 0x05]
        
        if topo_name == "star":
            self.current_topology = builders[topo_name](0x02, [d for d in devices if d != 0x02])
        elif topo_name == "ring":
            self.current_topology = builders[topo_name](0x01, devices[1:])
        elif topo_name == "mesh":
            self.current_topology = builders[topo_name](devices)
        elif topo_name == "tree":
            self.current_topology = builders[topo_name](0x01, [[0x02, 0x03], [0x04, 0x05]])
        elif topo_name == "point-to-point":
            self.current_topology = builders[topo_name](src, dst)
        elif topo_name == "bus":
            self.current_topology = builders[topo_name](devices)

        if self.current_topology:
            self.canvas.draw_topology(self.current_topology, 700, 400)

    def _start_simulation(self) -> None:
        """Start simulation."""
        if self.simulation_running:
            return

        self.simulation_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="● Running", foreground=COLORS["success"])
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.start()

        self.simulation_thread = threading.Thread(target=self._simulation_worker, daemon=True)
        self.simulation_thread.start()

        self._update_metrics_display()

    def _stop_simulation(self) -> None:
        """Stop simulation."""
        self.simulation_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="● Stopped", foreground=COLORS["warning"])
        self.progress.stop()
        self.progress.pack_forget()

    def _simulation_worker(self) -> None:
        """Background simulation worker."""
        src = int(self.src_var.get(), 16)
        dst = int(self.dst_var.get(), 16)
        error_rate = float(self.error_rate_var.get()) / 100
        protocol = self.protocol_var.get()

        while self.simulation_running:
            packet_data = bytes([random.randint(0, 255) for _ in range(100)])

            if protocol == "SpaceWire":
                packet = SpaceWirePacket(src=src, dst=dst, data=packet_data)
            else:
                packet = SpaceFibrePacket(src=src, dst=dst, data=packet_data)

            self.metrics.record_sent(len(packet.data))

            has_error = packet.simulate_error(error_rate)
            if has_error:
                self.metrics.record_error()

            latency = random.uniform(0.001, 0.01)
            self.metrics.record_received(latency, len(packet.data))

            self._log_message(f"Sent {protocol} packet: {packet}")

            if self.current_topology:
                path = self.current_topology.bfs_path(src, dst)
                if path:
                    self.root.after(0, lambda p=path: self.canvas.animate_packet(p))

            time.sleep(0.5)

    def _update_metrics_display(self) -> None:
        """Update metrics display."""
        if not self.simulation_running:
            return

        summary = self.metrics.get_summary()
        
        self.metric_labels["packets_sent"].config(text=str(summary["packets_sent"]))
        self.metric_labels["packets_received"].config(text=str(summary["packets_received"]))
        self.metric_labels["errors_detected"].config(text=str(summary["errors_detected"]))
        self.metric_labels["error_rate"].config(text=f"{summary['error_rate_percent']:.1f}%")
        self.metric_labels["avg_latency"].config(text=f"{summary['avg_latency_sec']*1000:.2f} ms")
        self.metric_labels["throughput"].config(text=f"{summary['throughput_pps']:.1f} pps")
        self.metric_labels["power"].config(text=f"{summary['power_consumption_mw']:.1f}")

        self.root.after(500, self._update_metrics_display)

    def _log_message(self, message: str) -> None:
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.reset()
        self._log_message("Metrics reset")
        for label in self.metric_labels.values():
            label.config(text="0")

    def _load_config(self) -> None:
        """Load configuration from file."""
        filepath = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("Config files", "*.yaml *.json"), ("All files", "*.*")]
        )
        if filepath:
            self.config = get_config(filepath)
            self._log_message(f"Loaded config: {filepath}")

    def _save_config(self) -> None:
        """Save configuration to file."""
        filepath = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml"), ("JSON", "*.json")]
        )
        if filepath:
            self.config.save(filepath)
            self._log_message(f"Saved config: {filepath}")

    def _export_metrics(self) -> None:
        """Export metrics to file."""
        filepath = filedialog.asksaveasfilename(
            title="Export Metrics",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv")]
        )
        if filepath:
            if filepath.endswith(".json"):
                self.metrics.export_json(filepath)
            else:
                self.metrics.export_csv(filepath)
            self._log_message(f"Exported metrics: {filepath}")

    def _load_file(self) -> None:
        """Load file for transmission."""
        filepath = filedialog.askopenfilename(title="Select File")
        if filepath:
            self._log_message(f"Selected file: {filepath}")

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "SpaceWire/SpaceFibre Network Simulator\n\n"
            "Version 1.0.0\n\n"
            "A comprehensive simulation toolkit for spacecraft "
            "communication networks."
        )


def main():
    """Main entry point."""
    root = tk.Tk()
    app = SpaceWireGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
