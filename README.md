# SpaceWire/SpaceFibre Network Simulator

A comprehensive simulation toolkit for spacecraft communication networks implementing SpaceWire and SpaceFibre protocols.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

## Overview

This project provides a complete simulation environment for SpaceWire and SpaceFibre networks, including:

- **Protocol Implementation**: Full SpaceWire and SpaceFibre packet definitions with CRC error detection
- **Network Topologies**: Support for Star, Ring, Mesh, Tree, Bus, and Point-to-Point configurations
- **Routing Algorithms**: BFS and Dijkstra's shortest path algorithms
- **Quality of Service (QoS)**: Priority-based packet handling with virtual channels
- **Metrics Collection**: Comprehensive performance and error tracking
- **Visual GUI**: Modern Tkinter-based graphical interface
- **CLI Tools**: Command-line tools for automation

## Architecture

```
spacewire/
├── spacewire/           # Main package
│   ├── __init__.py     # Package initialization
│   ├── packet.py       # SpaceWire/SpaceFibre packet implementations
│   ├── topology.py     # Network topology definitions & routing
│   ├── metrics.py      # Metrics collection & analysis
│   ├── config.py       # Configuration management
│   ├── logging_config.py # Logging setup
│   ├── gui.py          # Tkinter GUI application
│   ├── cli.py          # Command-line interface
│   └── config/         # Configuration files
├── tests/              # Unit tests
├── .github/workflows/  # CI/CD configuration
└── setup.py           # Package setup
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/eternalumin/spacewire.git
cd spacewire

# Install in development mode
pip install -e ".[dev]"

# Or install production version
pip install -e .
```

### Install Dependencies Only

```bash
pip install -r requirements.txt
```

## Usage

### GUI Application

Launch the graphical user interface:

```bash
spacewire-gui
# or
python -m spacewire.gui
```

### CLI Commands

#### Send Packets

```bash
# Send 10 packets from node 0x01 to 0x03
spacewire send 0x01 0x03 -c 10

# Send with SpaceFibre protocol
spacewire send 0x01 0x03 --protocol spacefibre --vc 2

# Custom packet count and error rate
spacewire send 0x01 0x03 -c 100 --error-rate 0.05 -o metrics.json
```

#### Show Topology

```bash
# Display mesh topology
spacewire topology mesh -v

# Display star topology
spacewire topology star
```

#### View Metrics

```bash
# Display metrics from file
spacewire metrics -i metrics.json

# Output as JSON
spacewire metrics -i metrics.json -f json
```

## Features

### Network Topologies

| Topology | Description | Use Case |
|----------|-------------|----------|
| Star | Central hub connected to all nodes | Simple hierarchical networks |
| Ring | Nodes connected in a circle | Redundant pathways |
| Mesh | Full connectivity between nodes | High reliability |
| Tree | Hierarchical structure | Distributed systems |
| Bus | Single backbone with drop lines | Simple networks |
| Point-to-Point | Direct connection | Direct links |

### Protocol Support

#### SpaceWire
- CRC-8 error detection
- Packet routing
- Priority levels
- Time code support

#### SpaceFibre (Enhanced)
- CRC-16 error detection
- Virtual channels (8)
- QoS scheduling
- Flow control
- Higher throughput

### Quality of Service

Four priority levels:
- **Critical (0)**: Highest priority - 40% bandwidth
- **High (1)**: Time-critical - 30% bandwidth
- **Normal (2)**: Standard traffic - 20% bandwidth
- **Low (3)**: Best-effort - 10% bandwidth

## Configuration

### YAML Configuration

```yaml
network:
  interface: "eth0"
  chunk_size: 1000

simulation:
  error_rate: 0.1
  topology: "mesh"

qos:
  enabled: true
  virtual_channels: 8
```

### Load Custom Configuration

```bash
spacewire-gui -c config/my_config.yaml
```

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=spacewire

# Run specific test file
pytest tests/test_packet.py -v
```

### Code Quality

```bash
# Format code with Black
black spacewire/

# Type checking
mypy spacewire/
```

### CI/CD

The project includes GitHub Actions workflows for:
- Multi-platform testing (Ubuntu, Windows, macOS)
- Multiple Python versions (3.8-3.12)
- Code formatting checks
- Type checking
- Coverage reporting

## API Usage

### Creating Packets

```python
from spacewire.packet import SpaceWirePacket, PacketFactory, PacketPriority

# Create individual packet
packet = SpaceWirePacket(
    src=0x01,
    dst=0x02,
    data=b"Hello, SpaceWire!",
    priority=PacketPriority.HIGH
)

# Verify integrity
if packet.verify():
    print("Packet is valid!")

# Serialize to bytes
data = packet.to_bytes()

# Create batch from file
packets = PacketFactory.create_batch(
    src=0x01,
    dst=0x02,
    file_data=file_content,
    chunk_size=1000,
    protocol="spacefibre",
    virtual_channel=2
)
```

### Building Topologies

```python
from spacewire.topology import TopologyBuilder, get_topology

# Create star topology
topo = TopologyBuilder.star(hub_id=0x01, device_ids=[0x02, 0x03, 0x04])

# Find shortest path
path = topo.bfs_path(0x01, 0x04)

# Legacy interface
edges = get_topology("mesh", [0x01, 0x02, 0x03, 0x04])
```

### Collecting Metrics

```python
from spacewire.metrics import MetricsCollector

metrics = MetricsCollector()

# Record events
metrics.record_sent(packet_size)
metrics.record_received(latency, size)
metrics.record_error()

# Get statistics
summary = metrics.get_summary()
print(f"Throughput: {summary['throughput_pps']} pps")
print(f"Error Rate: {summary['error_rate_percent']}%")

# Export
metrics.export_json("metrics.json")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## References

- [SpaceWire Standard](https://www.esa.int/ESA_Connectors/SpaceWire) - European Space Agency
- [SpaceFibre Standard](https://www.esa.int/ESA_Connectors/SpaceFibre) - High-speed SpaceWire evolution
- [Scapy Documentation](https://scapy.readthedocs.io/) - Packet manipulation library

## Acknowledgments

This project was developed as a simulation toolkit for spacecraft communication networks, providing educational and research capabilities for understanding SpaceWire and SpaceFibre protocols.
