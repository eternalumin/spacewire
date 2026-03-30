"""Unit tests for topology module."""

import pytest
from spacewire.topology import (
    Topology, TopologyType, Node, TopologyBuilder,
    get_topology, format_node_id
)


class TestNode:
    """Tests for Node class."""

    def test_create_node(self):
        """Test node creation."""
        node = Node(id=1, name="TestNode", x=10.0, y=20.0)
        assert node.id == 1
        assert node.name == "TestNode"
        assert node.x == 10.0
        assert node.y == 20.0

    def test_node_hash(self):
        """Test node hashing."""
        node1 = Node(id=1, name="Node1")
        node2 = Node(id=1, name="Node2")
        assert hash(node1) == hash(node2)

    def test_node_equality(self):
        """Test node equality."""
        node1 = Node(id=1, name="Node1")
        node2 = Node(id=1, name="Node2")
        assert node1 == node2


class TestTopology:
    """Tests for Topology class."""

    def test_create_topology(self):
        """Test topology creation."""
        topo = Topology("Test", TopologyType.MESH)
        assert topo.name == "Test"
        assert topo.topology_type == TopologyType.MESH

    def test_add_node(self):
        """Test adding nodes."""
        topo = Topology("Test", TopologyType.MESH)
        node = Node(id=1, name="Node1")
        topo.add_node(node)
        assert 1 in topo.nodes

    def test_add_edge(self):
        """Test adding edges."""
        topo = Topology("Test", TopologyType.MESH)
        topo.add_node(Node(id=1, name="Node1"))
        topo.add_node(Node(id=2, name="Node2"))
        topo.add_edge(1, 2)
        assert 2 in topo.edges[1]
        assert 1 in topo.edges[2]

    def test_get_neighbors(self):
        """Test getting neighbors."""
        topo = Topology("Test", TopologyType.MESH)
        topo.add_node(Node(id=1, name="Node1"))
        topo.add_node(Node(id=2, name="Node2"))
        topo.add_node(Node(id=3, name="Node3"))
        topo.add_edge(1, 2)
        topo.add_edge(1, 3)
        neighbors = topo.get_neighbors(1)
        assert 2 in neighbors
        assert 3 in neighbors


class TestTopologyBuilder:
    """Tests for TopologyBuilder."""

    def test_star_topology(self):
        """Test star topology creation."""
        topo = TopologyBuilder.star(0x01, [0x02, 0x03, 0x04])
        assert len(topo.nodes) == 4
        assert topo.is_connected()

    def test_ring_topology(self):
        """Test ring topology creation."""
        topo = TopologyBuilder.ring(0x01, [0x02, 0x03, 0x04])
        assert len(topo.nodes) == 4

    def test_mesh_topology(self):
        """Test mesh topology creation."""
        topo = TopologyBuilder.mesh([0x01, 0x02, 0x03])
        assert len(topo.nodes) == 3

    def test_tree_topology(self):
        """Test tree topology creation."""
        topo = TopologyBuilder.tree(0x01, [[0x02, 0x03], [0x04, 0x05]])
        assert len(topo.nodes) == 5

    def test_point_to_point(self):
        """Test point-to-point topology."""
        topo = TopologyBuilder.point_to_point(0x01, 0x02)
        assert len(topo.nodes) == 2

    def test_bus_topology(self):
        """Test bus topology."""
        topo = TopologyBuilder.bus([0x01, 0x02, 0x03])
        assert len(topo.nodes) == 3


class TestPathfinding:
    """Tests for pathfinding algorithms."""

    def test_bfs_path(self):
        """Test BFS pathfinding."""
        topo = TopologyBuilder.mesh([0x01, 0x02, 0x03, 0x04])
        path = topo.bfs_path(0x01, 0x04)
        assert path is not None
        assert path[0] == 0x01
        assert path[-1] == 0x04

    def test_bfs_no_path(self):
        """Test BFS with no path."""
        topo = Topology("Test", TopologyType.MESH)
        topo.add_node(Node(id=1, name="N1"))
        topo.add_node(Node(id=2, name="N2"))
        path = topo.bfs_path(1, 2)
        assert path is None

    def test_dijkstra_path(self):
        """Test Dijkstra pathfinding."""
        topo = TopologyBuilder.mesh([0x01, 0x02, 0x03, 0x04])
        path = topo.dijkstra_path(0x01, 0x04)
        assert path is not None
        assert path[0] == 0x01
        assert path[-1] == 0x04


class TestTopologyValidation:
    """Tests for topology validation."""

    def test_validate_empty(self):
        """Test validation of empty topology."""
        topo = Topology("Test", TopologyType.MESH)
        is_valid, errors = topo.validate()
        assert not is_valid

    def test_validate_connected(self):
        """Test validation of connected topology."""
        topo = TopologyBuilder.mesh([0x01, 0x02])
        is_valid, errors = topo.validate()
        assert is_valid


class TestHelpers:
    """Tests for helper functions."""

    def test_format_node_id(self):
        """Test node ID formatting."""
        assert format_node_id(1) == "0x001"
        assert format_node_id(255) == "0x255"

    def test_get_topology_legacy(self):
        """Test legacy get_topology function."""
        edges = get_topology("point-to-point", 0x01, 0x02)
        assert 0x01 in edges
        assert 0x02 in edges[0x01]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
