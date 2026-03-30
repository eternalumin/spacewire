"""Network topology definitions and routing algorithms."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Any
from enum import Enum
from collections import deque
import random


class TopologyType(Enum):
    """Supported network topology types."""
    STAR = "star"
    RING = "ring"
    MESH = "mesh"
    TREE = "tree"
    POINT_TO_POINT = "point-to-point"
    BUS = "bus"
    HYBRID = "hybrid"


@dataclass
class Node:
    """Represents a network node in the topology."""
    id: int
    name: str
    x: float = 0.0
    y: float = 0.0
    connections: List["Node"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass
class Topology:
    """Represents a network topology with nodes and connections."""
    name: str
    topology_type: TopologyType
    nodes: Dict[int, Node] = field(default_factory=dict)
    edges: Dict[int, List[int]] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        """Add a node to the topology."""
        self.nodes[node.id] = node

    def add_edge(self, src_id: int, dst_id: int, bidirectional: bool = True) -> None:
        """Add an edge between two nodes."""
        if src_id not in self.edges:
            self.edges[src_id] = []
        if dst_id not in self.edges:
            self.edges[dst_id] = []

        if dst_id not in self.edges[src_id]:
            self.edges[src_id].append(dst_id)
        if bidirectional and src_id not in self.edges[dst_id]:
            self.edges[dst_id].append(src_id)

        if src_id in self.nodes and dst_id in self.nodes:
            self.nodes[src_id].connections.append(self.nodes[dst_id])
            if bidirectional:
                self.nodes[dst_id].connections.append(self.nodes[src_id])

    def get_neighbors(self, node_id: int) -> List[int]:
        """Get neighboring nodes."""
        return self.edges.get(node_id, [])

    def bfs_path(self, src_id: int, dst_id: int) -> Optional[List[int]]:
        """Find shortest path using BFS."""
        if src_id not in self.edges or dst_id not in self.edges:
            return None

        queue = deque([(src_id, [src_id])])
        visited: Set[int] = {src_id}

        while queue:
            current, path = queue.popleft()
            if current == dst_id:
                return path

            for neighbor in self.edges.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def dijkstra_path(
        self, src_id: int, dst_id: int, weights: Optional[Dict[Tuple[int, int], float]] = None
    ) -> Optional[List[int]]:
        """Find shortest path using Dijkstra's algorithm."""
        if src_id not in self.edges or dst_id not in self.edges:
            return None

        import heapq

        distances: Dict[int, float] = {src_id: 0}
        previous: Dict[int, Optional[int]] = {src_id: None}
        heap = [(0, src_id)]

        while heap:
            current_dist, current = heapq.heappop(heap)

            if current_dist > distances.get(current, float('inf')):
                continue

            if current == dst_id:
                break

            for neighbor in self.edges.get(current, []):
                weight = weights.get((current, neighbor), 1) if weights else 1
                distance = current_dist + weight

                if distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(heap, (distance, neighbor))

        if dst_id not in previous:
            return None

        path = []
        current = dst_id
        while current is not None:
            path.append(current)
            current = previous[current]
        return list(reversed(path))

    def is_connected(self) -> bool:
        """Check if topology is fully connected."""
        if not self.nodes:
            return True
        visited: Set[int] = set()
        queue = deque([next(iter(self.nodes))])

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(self.edges.get(node, []))

        return len(visited) == len(self.nodes)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate topology configuration."""
        errors: List[str] = []

        if not self.nodes:
            errors.append("Topology has no nodes")

        if not self.is_connected():
            errors.append("Topology is not fully connected")

        for src, dsts in self.edges.items():
            if src not in self.nodes:
                errors.append(f"Edge source {src} not in nodes")

        return len(errors) == 0, errors


class TopologyBuilder:
    """Builder class for creating standard topologies."""

    @staticmethod
    def star(hub_id: int, device_ids: List[int]) -> Topology:
        """Create a star topology."""
        topo = Topology("Star", TopologyType.STAR)

        for did in device_ids:
            topo.add_node(Node(id=did, name=f"Node_{did:02X}"))

        for did in device_ids:
            topo.add_edge(hub_id, did, bidirectional=False)

        return topo

    @staticmethod
    def ring(start_id: int, device_ids: List[int]) -> Topology:
        """Create a ring topology."""
        topo = Topology("Ring", TopologyType.RING)
        all_ids = [start_id] + device_ids

        for did in all_ids:
            topo.add_node(Node(id=did, name=f"Node_{did:02X}"))

        for i in range(len(all_ids)):
            src = all_ids[i]
            dst = all_ids[(i + 1) % len(all_ids)]
            topo.add_edge(src, dst, bidirectional=False)

        return topo

    @staticmethod
    def mesh(device_ids: List[int]) -> Topology:
        """Create a full mesh topology."""
        topo = Topology("Mesh", TopologyType.MESH)

        for did in device_ids:
            topo.add_node(Node(id=did, name=f"Node_{did:02X}"))

        for i, src in enumerate(device_ids):
            for dst in device_ids[i + 1:]:
                topo.add_edge(src, dst)

        return topo

    @staticmethod
    def tree(root_id: int, levels: List[List[int]]) -> Topology:
        """Create a tree topology."""
        topo = Topology("Tree", TopologyType.TREE)
        topo.add_node(Node(id=root_id, name=f"Root_{root_id:02X}"))

        for level_nodes in levels:
            for did in level_nodes:
                topo.add_node(Node(id=did, name=f"Node_{did:02X}"))

        parent_id = root_id
        for level_nodes in levels:
            for did in level_nodes:
                topo.add_edge(parent_id, did, bidirectional=False)
            if level_nodes:
                parent_id = random.choice(level_nodes)

        return topo

    @staticmethod
    def point_to_point(src_id: int, dst_id: int) -> Topology:
        """Create a point-to-point topology."""
        topo = Topology("Point-to-Point", TopologyType.POINT_TO_POINT)
        topo.add_node(Node(id=src_id, name=f"Src_{src_id:02X}"))
        topo.add_node(Node(id=dst_id, name=f"Dst_{dst_id:02X}"))
        topo.add_edge(src_id, dst_id, bidirectional=False)
        return topo

    @staticmethod
    def bus(device_ids: List[int]) -> Topology:
        """Create a bus topology."""
        topo = Topology("Bus", TopologyType.BUS)

        for did in device_ids:
            topo.add_node(Node(id=did, name=f"Node_{did:02X}"))

        for did in device_ids:
            topo.add_edge(0x00, did, bidirectional=False)

        return topo


def get_topology(
    topology_name: str,
    *args,
    **kwargs,
) -> Dict[int, List[int]]:
    """
    Get topology as adjacency dictionary (legacy interface).
    
    Args:
        topology_name: Name of the topology
        *args: Additional arguments for topology creation
        **kwargs: Additional keyword arguments
    
    Returns:
        Dictionary mapping source nodes to destination lists
    """
    builders = {
        "star": TopologyBuilder.star,
        "ring": TopologyBuilder.ring,
        "mesh": TopologyBuilder.mesh,
        "tree": TopologyBuilder.tree,
        "point-to-point": TopologyBuilder.point_to_point,
        "bus": TopologyBuilder.bus,
    }

    if topology_name not in builders:
        raise ValueError(f"Invalid topology: {topology_name}. Valid options: {list(builders.keys())}")

    topo = builders[topology_name](*args, **kwargs)
    return topo.edges


def format_node_id(n: int) -> str:
    """Format node ID as hex string."""
    return f"0x{int(n):03d}"
