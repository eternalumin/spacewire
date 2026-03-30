"""Unit tests for metrics module."""

import pytest
import time
import json
import os
from spacewire.metrics import (
    MetricsCollector, QoSMetrics, MetricsSnapshot, MetricType
)


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_create_collector(self):
        """Test creating a metrics collector."""
        metrics = MetricsCollector()
        assert metrics.packets_sent == 0
        assert metrics.packets_received == 0
        assert metrics.errors_detected == 0

    def test_record_sent(self):
        """Test recording sent packets."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        assert metrics.packets_sent == 1
        assert metrics.bytes_transferred == 100

    def test_record_received(self):
        """Test recording received packets."""
        metrics = MetricsCollector()
        metrics.record_received(0.001, 100)
        assert metrics.packets_received == 1

    def test_record_error(self):
        """Test recording errors."""
        metrics = MetricsCollector()
        metrics.record_error()
        assert metrics.errors_detected == 1

    def test_reset(self):
        """Test resetting metrics."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        metrics.record_error()
        metrics.reset()
        assert metrics.packets_sent == 0
        assert metrics.errors_detected == 0

    def test_get_avg_latency(self):
        """Test average latency calculation."""
        metrics = MetricsCollector()
        metrics.record_received(0.001, 100)
        metrics.record_received(0.002, 100)
        metrics.record_received(0.003, 100)
        avg = metrics.get_avg_latency()
        assert abs(avg - 0.002) < 0.0001

    def test_latency_stats(self):
        """Test latency statistics."""
        metrics = MetricsCollector()
        latencies = [0.001, 0.002, 0.003, 0.004, 0.005]
        for lat in latencies:
            metrics.record_received(lat, 100)
        
        stats = metrics.get_latency_stats()
        assert stats["min"] == 0.001
        assert stats["max"] == 0.005

    def test_get_throughput(self):
        """Test throughput calculation."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        metrics.record_sent(100)
        time.sleep(0.1)
        throughput = metrics.get_throughput()
        assert throughput > 0

    def test_get_error_rate(self):
        """Test error rate calculation."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        metrics.record_error()
        metrics.record_error()
        error_rate = metrics.get_error_rate()
        assert error_rate == 2.0

    def test_power_estimation(self):
        """Test power consumption estimation."""
        metrics = MetricsCollector()
        metrics.record_received(0.001, 100)
        power = metrics.estimate_power_consumption(base_power=10.0, latency_factor=5000.0)
        assert power > 10.0

    def test_get_summary(self):
        """Test metrics summary."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        metrics.record_received(0.001, 100)
        metrics.record_error()
        
        summary = metrics.get_summary()
        assert "packets_sent" in summary
        assert "packets_received" in summary
        assert "errors_detected" in summary

    def test_snapshot(self):
        """Test taking snapshots."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        snapshot = metrics.take_snapshot()
        assert snapshot.packets_sent == 1
        assert isinstance(snapshot.timestamp, float)

    def test_export_json(self, tmp_path):
        """Test JSON export."""
        metrics = MetricsCollector()
        metrics.record_sent(100)
        
        filepath = tmp_path / "metrics.json"
        metrics.export_json(str(filepath))
        
        assert filepath.exists()
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        assert "summary" in data


class TestQoSMetrics:
    """Tests for QoS metrics."""

    def test_create_qos_metrics(self):
        """Test creating QoS metrics."""
        qos = QoSMetrics()
        assert qos._priority_counts[0] == 0

    def test_record_priority(self):
        """Test recording priority metrics."""
        qos = QoSMetrics()
        qos.record_priority(1, 0.001)
        qos.record_priority(1, 0.002)
        stats = qos.get_priority_stats()
        assert stats[1]["count"] == 2


class TestMetricsSnapshot:
    """Tests for MetricsSnapshot."""

    def test_create_snapshot(self):
        """Test creating a snapshot."""
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            packets_sent=10,
            packets_received=8,
            errors_detected=2,
            total_latency=0.01,
            bytes_transferred=1000
        )
        assert snapshot.packets_sent == 10

    def test_snapshot_avg_latency(self):
        """Test snapshot average latency."""
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            packets_sent=10,
            packets_received=5,
            total_latency=0.01
        )
        assert snapshot.avg_latency == 0.002

    def test_snapshot_error_rate(self):
        """Test snapshot error rate."""
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            packets_sent=10,
            errors_detected=1
        )
        assert snapshot.error_rate == 10.0

    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        snapshot = MetricsSnapshot(
            timestamp=1234567890.0,
            packets_sent=10
        )
        data = snapshot.to_dict()
        assert data["packets_sent"] == 10
        assert data["timestamp"] == 1234567890.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
