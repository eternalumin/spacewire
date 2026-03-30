"""Configuration management for SpaceWire simulation."""

import os
import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class NetworkConfig:
    """Network configuration settings."""
    interface: str = "eth0"
    protocol_id: int = 0x88B5
    mtu: int = 1500
    chunk_size: int = 1000
    timeout: float = 30.0
    retry_count: int = 3


@dataclass
class SimulationConfig:
    """Simulation configuration settings."""
    error_rate: float = 0.1
    latency_base: float = 0.001
    latency_variance: float = 0.0001
    packet_delay: float = 0.5
    topology: str = "point-to-point"


@dataclass
class QoSConfig:
    """Quality of Service configuration."""
    enabled: bool = True
    num_priorities: int = 4
    virtual_channels: int = 8
    bandwidth_allocation: Dict[int, float] = field(default_factory=lambda: {
        0: 0.4,  # Critical
        1: 0.3,  # High
        2: 0.2,  # Normal
        3: 0.1,  # Low
    })


@dataclass
class GUIConfig:
    """GUI configuration settings."""
    window_width: int = 1200
    window_height: int = 800
    theme: str = "dark"
    animation_speed: int = 30
    show_metrics: bool = True
    auto_refresh_interval: int = 1000


@dataclass
class Config:
    """Main configuration container."""
    network: NetworkConfig = field(default_factory=NetworkConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    qos: QoSConfig = field(default_factory=QoSConfig)
    gui: GUIConfig = field(default_factory=GUIConfig)
    devices: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        return cls(
            network=NetworkConfig(**data.get("network", {})),
            simulation=SimulationConfig(**data.get("simulation", {})),
            qos=QoSConfig(**data.get("qos", {})),
            gui=GUIConfig(**data.get("gui", {})),
            devices=data.get("devices", []),
        )

    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Load configuration from file."""
        path = Path(filepath)
        
        if not path.exists():
            return cls.get_default()

        with open(path, 'r') as f:
            if path.suffix in ('.yaml', '.yml'):
                data = yaml.safe_load(f)
            elif path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")

        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "network": self.network.__dict__,
            "simulation": self.simulation.__dict__,
            "qos": self.qos.__dict__,
            "gui": self.gui.__dict__,
            "devices": self.devices,
        }

    def save(self, filepath: str) -> None:
        """Save configuration to file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            if path.suffix in ('.yaml', '.yml'):
                yaml.dump(self.to_dict(), f, default_flow_style=False)
            elif path.suffix == '.json':
                json.dump(self.to_dict(), f, indent=2)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")

    @classmethod
    def get_default(cls) -> "Config":
        """Get default configuration."""
        config = cls()
        config.devices = [
            {"id": 0x01, "name": "OBC", "type": "computer", "x": 150, "y": 300},
            {"id": 0x02, "name": "Router", "type": "router", "x": 350, "y": 100},
            {"id": 0x03, "name": "Camera", "type": "sensor", "x": 550, "y": 100},
            {"id": 0x04, "name": "SSD", "type": "storage", "x": 350, "y": 500},
            {"id": 0x05, "name": "AOCS", "type": "sensor", "x": 550, "y": 500},
        ]
        return config


_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get global configuration instance."""
    global _config
    
    if _config is not None:
        return _config

    if config_path and os.path.exists(config_path):
        _config = Config.from_file(config_path)
    else:
        default_paths = [
            "config/default.yaml",
            "config/default.json",
            os.path.expanduser("~/.spacewire/config.yaml"),
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                _config = Config.from_file(path)
                return _config

        _config = Config.get_default()
    
    return _config


def set_config(config: Config) -> None:
    """Set global configuration instance."""
    global _config
    _config = Config.get_default()
    _config = config
