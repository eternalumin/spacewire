"""Command-line interface for SpaceWire simulation."""

import argparse
import sys
import json
from pathlib import Path

from spacewire.topology import TopologyBuilder, get_topology
from spacewire.packet import SpaceWirePacket, SpaceFibrePacket, PacketFactory, PacketPriority
from spacewire.metrics import MetricsCollector
from spacewire.config import Config, get_config
from spacewire.logging_config import setup_logging, get_logger


def cmd_send(args) -> None:
    """Send packets between nodes."""
    logger = get_logger("cli")
    metrics = MetricsCollector()

    src = int(args.src, 16) if isinstance(args.src, str) else args.src
    dst = int(args.dst, 16) if isinstance(args.dst, str) else args.dst
    num_packets = args.count
    chunk_size = args.chunk_size

    logger.info(f"Sending {num_packets} packets from 0x{src:02X} to 0x{dst:02X}")

    for i in range(num_packets):
        data = bytes([(i + j) % 256 for j in range(chunk_size)])
        
        if args.protocol == "spacefibre":
            packet = PacketFactory.create_spacefibre(
                src, dst, data,
                virtual_channel=args.vc,
                priority=PacketPriority(args.priority)
            )
        else:
            packet = PacketFactory.create_spacewire(
                src, dst, data,
                priority=PacketPriority(args.priority)
            )

        metrics.record_sent(len(data))
        
        has_error = packet.simulate_error(args.error_rate)
        if has_error:
            metrics.record_error()
        
        latency = 0.001 + (i * 0.0001)
        metrics.record_received(latency, len(data))

        logger.debug(f"Sent packet {i+1}/{num_packets}: {packet}")

    summary = metrics.get_summary()
    print(json.dumps(summary, indent=2))

    if args.output:
        metrics.export_json(args.output)


def cmd_topology(args) -> None:
    """Display topology information."""
    logger = get_logger("cli")

    topology_funcs = {
        "star": lambda: TopologyBuilder.star(0x02, [0x01, 0x03, 0x04, 0x05]),
        "ring": lambda: TopologyBuilder.ring(0x01, [0x02, 0x03, 0x04, 0x05]),
        "mesh": lambda: TopologyBuilder.mesh([0x01, 0x02, 0x03, 0x04, 0x05]),
        "tree": lambda: TopologyBuilder.tree(0x01, [[0x02, 0x03], [0x04, 0x05]]),
        "point-to-point": lambda: TopologyBuilder.point_to_point(0x01, 0x03),
        "bus": lambda: TopologyBuilder.bus([0x01, 0x02, 0x03, 0x04, 0x05]),
    }

    if args.type not in topology_funcs:
        logger.error(f"Unknown topology: {args.type}")
        sys.exit(1)

    topo = topology_funcs[args.type]()

    print(f"\n=== {args.type.capitalize()} Topology ===")
    print(f"Nodes: {len(topo.nodes)}")
    print(f"Edges: {sum(len(v) for v in topo.edges.values())}")
    print(f"Connected: {topo.is_connected()}")

    if args.verbose:
        print("\nNode Details:")
        for node_id, node in topo.nodes.items():
            print(f"  0x{node_id:02X}: {node.name} - {len(topo.get_neighbors(node_id))} connections")


def cmd_metrics(args) -> None:
    """Display metrics."""
    if args.input:
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        if args.format == "json":
            print(json.dumps(data, indent=2))
        else:
            summary = data.get("summary", {})
            print("\n=== Metrics Summary ===")
            for key, value in summary.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key}: {value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SpaceWire/SpaceFibre Network Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "-c", "--config",
        help="Configuration file path"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    send_parser = subparsers.add_parser("send", help="Send packets")
    send_parser.add_argument("src", help="Source node ID (hex)")
    send_parser.add_argument("dst", help="Destination node ID (hex)")
    send_parser.add_argument("-c", "--count", type=int, default=10, help="Number of packets")
    send_parser.add_argument("-p", "--protocol", choices=["spacewire", "spacefibre"], default="spacewire")
    send_parser.add_argument("--priority", type=int, choices=[0, 1, 2, 3], default=2)
    send_parser.add_argument("--vc", type=int, default=0, help="Virtual channel (SpaceFibre)")
    send_parser.add_argument("--chunk-size", type=int, default=1000)
    send_parser.add_argument("--error-rate", type=float, default=0.1)
    send_parser.add_argument("-o", "--output", help="Output file for metrics")

    topo_parser = subparsers.add_parser("topology", help="Show topology")
    topo_parser.add_argument("type", choices=["star", "ring", "mesh", "tree", "point-to-point", "bus"])
    topo_parser.add_argument("-v", "--verbose", action="store_true")

    metrics_parser = subparsers.add_parser("metrics", help="Show metrics")
    metrics_parser.add_argument("-i", "--input", required=True)
    metrics_parser.add_argument("-f", "--format", choices=["json", "text"], default="text")

    args = parser.parse_args()

    log_level = 10 if args.verbose else 20
    setup_logging(level=log_level)

    if hasattr(args, "config") and args.config:
        get_config(args.config)

    if args.command == "send":
        cmd_send(args)
    elif args.command == "topology":
        cmd_topology(args)
    elif args.command == "metrics":
        cmd_metrics(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
