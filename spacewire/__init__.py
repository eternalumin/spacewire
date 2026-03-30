"""
SpaceWire/SpaceFibre Network Simulation Package

A comprehensive simulation toolkit for spacecraft communication networks
implementing SpaceWire and SpaceFibre protocols.
"""

__version__ = "1.0.0"
__author__ = "SpaceWire Team"

from spacewire.packet import SpaceWirePacket, SpaceFibrePacket, CRC8, CRC16
from spacewire.topology import Topology, get_topology
from spacewire.metrics import MetricsCollector, MetricsSnapshot

__all__ = [
    "SpaceWirePacket",
    "SpaceFibrePacket",
    "CRC8",
    "CRC16",
    "Topology",
    "get_topology",
    "MetricsCollector",
    "MetricsSnapshot",
]
