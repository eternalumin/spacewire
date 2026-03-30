"""Metrics collection and analysis for network simulation."""

import time
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import statistics


class MetricType(Enum):
    """Types of metrics tracked."""
    PACKETS_SENT = "packets_sent"
    PACKETS_RECEIVED = "packets_received"
    ERRORS_DETECTED = "errors_detected"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    POWER_CONSUMPTION = "power_consumption"
    BANDWIDTH = "bandwidth"
    QUEUE_LENGTH = "queue_length"


@dataclass
class MetricsSnapshot:
    """Point-in-time snapshot of metrics."""
    timestamp: float
    packets_sent: int = 0
    packets_received: int = 0
    errors_detected: int = 0
    total_latency: float = 0.0
    bytes_transferred: int = 0

    @property
    def avg_latency(self) -> float:
        return self.total_latency / self.packets_received if self.packets_received > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return (self.errors_detected / self.packets_sent * 100) if self.packets_sent > 0 else 0.0

    @property
    def throughput(self) -> float:
        return self.packets_sent / self.total_latency if self.total_latency > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "errors_detected": self.errors_detected,
            "avg_latency": self.avg_latency,
            "error_rate": self.error_rate,
            "throughput": self.throughput,
            "bytes_transferred": self.bytes_transferred,
        }


@dataclass
class MetricsCollector:
    """
    Thread-safe metrics collector for network simulation.
    
    Provides comprehensive metrics tracking including:
    - Packet counts (sent, received, errors)
    - Latency measurements
    - Throughput calculations
    - Power consumption estimation
    """

    _lock = threading.Lock()

    def __init__(self):
        self._packets_sent = 0
        self._packets_received = 0
        self._errors_detected = 0
        self._latency_records: List[float] = []
        self._bytes_transferred = 0
        self._start_time = time.time()
        self._snapshots: List[MetricsSnapshot] = []
        self._event_log: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._packets_sent = 0
            self._packets_received = 0
            self._errors_detected = 0
            self._latency_records.clear()
            self._bytes_transferred = 0
            self._start_time = time.time()
            self._snapshots.clear()
            self._event_log.clear()

    def record_sent(self, packet_size: int) -> None:
        """Record a packet being sent."""
        with self._lock:
            self._packets_sent += 1
            self._bytes_transferred += packet_size

    def record_received(self, latency: float, packet_size: int) -> None:
        """Record a packet being received."""
        with self._lock:
            self._packets_received += 1
            self._latency_records.append(latency)

    def record_error(self) -> None:
        """Record an error detection."""
        with self._lock:
            self._errors_detected += 1

    def record_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Record a custom event."""
        with self._lock:
            self._event_log.append({
                "timestamp": time.time(),
                "type": event_type,
                "details": details,
            })

    def take_snapshot(self) -> MetricsSnapshot:
        """Take a snapshot of current metrics."""
        with self._lock:
            snapshot = MetricsSnapshot(
                timestamp=time.time(),
                packets_sent=self._packets_sent,
                packets_received=self._packets_received,
                errors_detected=self._errors_detected,
                total_latency=sum(self._latency_records),
                bytes_transferred=self._bytes_transferred,
            )
            self._snapshots.append(snapshot)
            return snapshot

    @property
    def packets_sent(self) -> int:
        return self._packets_sent

    @property
    def packets_received(self) -> int:
        return self._packets_received

    @property
    def errors_detected(self) -> int:
        return self._errors_detected

    @property
    def bytes_transferred(self) -> int:
        return self._bytes_transferred

    @property
    def runtime(self) -> float:
        return time.time() - self._start_time

    def get_avg_latency(self) -> float:
        """Get average latency."""
        with self._lock:
            if not self._latency_records:
                return 0.0
            return statistics.mean(self._latency_records)

    def get_latency_stats(self) -> Dict[str, float]:
        """Get detailed latency statistics."""
        with self._lock:
            if not self._latency_records:
                return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "stdev": 0.0}

            return {
                "min": min(self._latency_records),
                "max": max(self._latency_records),
                "mean": statistics.mean(self._latency_records),
                "median": statistics.median(self._latency_records),
                "stdev": statistics.stdev(self._latency_records) if len(self._latency_records) > 1 else 0.0,
            }

    def get_throughput(self) -> float:
        """Get throughput in packets per second."""
        runtime = self.runtime
        return self._packets_sent / runtime if runtime > 0 else 0.0

    def get_bandwidth(self) -> float:
        """Get bandwidth in bytes per second."""
        runtime = self.runtime
        return self._bytes_transferred / runtime if runtime > 0 else 0.0

    def get_error_rate(self) -> float:
        """Get error rate as percentage."""
        if self._packets_sent == 0:
            return 0.0
        return (self._errors_detected / self._packets_sent) * 100

    def estimate_power_consumption(self, base_power: float = 10.0, latency_factor: float = 5000.0) -> float:
        """
        Estimate power consumption in milliwatts.
        
        Simple model: base_power * (1 + latency_factor * avg_latency)
        """
        avg_latency = self.get_avg_latency()
        return base_power * (1 + latency_factor * avg_latency)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "errors_detected": self.errors_detected,
            "bytes_transferred": self.bytes_transferred,
            "runtime_seconds": self.runtime,
            "throughput_pps": self.get_throughput(),
            "bandwidth_bps": self.get_bandwidth(),
            "error_rate_percent": self.get_error_rate(),
            "avg_latency_sec": self.get_avg_latency(),
            "latency_stats": self.get_latency_stats(),
            "power_consumption_mw": self.estimate_power_consumption(),
        }

    def export_json(self, filename: str) -> None:
        """Export metrics to JSON file."""
        data = {
            "summary": self.get_summary(),
            "snapshots": [s.to_dict() for s in self._snapshots],
            "events": self._event_log,
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def export_csv(self, filename: str) -> None:
        """Export latency records to CSV."""
        with open(filename, 'w') as f:
            f.write("packet_id,latency_sec\n")
            for i, latency in enumerate(self._latency_records, 1):
                f.write(f"{i},{latency}\n")


class QoSMetrics:
    """Quality of Service metrics tracking."""

    def __init__(self):
        self._priority_counts: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self._priority_latencies: Dict[int, List[float]] = {0: [], 1: [], 2: [], 3: []}
        self._lock = threading.Lock()

    def record_priority(self, priority: int, latency: float) -> None:
        """Record metrics for a priority level."""
        with self._lock:
            if priority in self._priority_counts:
                self._priority_counts[priority] += 1
                self._priority_latencies[priority].append(latency)

    def get_priority_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics by priority level."""
        with self._lock:
            stats = {}
            for priority in self._priority_counts:
                latencies = self._priority_latencies[priority]
                if latencies:
                    stats[priority] = {
                        "count": self._priority_counts[priority],
                        "avg_latency": statistics.mean(latencies),
                        "min_latency": min(latencies),
                        "max_latency": max(latencies),
                    }
                else:
                    stats[priority] = {
                        "count": 0,
                        "avg_latency": 0.0,
                        "min_latency": 0.0,
                        "max_latency": 0.0,
                    }
            return stats
