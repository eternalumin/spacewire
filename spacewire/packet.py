"""SpaceWire and SpaceFibre packet implementations with CRC error detection."""

import random
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
import threading


try:
    from scapy.all import Packet as ScapyPacket, ByteField, StrLenField, ByteField as Byte
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False


class PacketPriority(Enum):
    """Packet priority levels for QoS."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class PacketType(Enum):
    """SpaceWire packet types."""
    DATA = 0x00
    CONTROL = 0x01
    TIME_CODE = 0x02


@dataclass
class PacketMetrics:
    """Metrics collected for each packet."""
    packet_id: int
    src: int
    dst: int
    size: int
    send_time: float
    receive_time: Optional[float] = None
    latency: Optional[float] = None
    error_detected: bool = False
    priority: PacketPriority = PacketPriority.NORMAL


class CRC8:
    """CRC-8 error detection implementation."""

    POLYNOMIAL = 0x07

    @staticmethod
    def calculate(data: bytes) -> int:
        """Calculate CRC-8 checksum for data."""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ CRC8.POLYNOMIAL
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc

    @staticmethod
    def verify(data: bytes, checksum: int) -> bool:
        """Verify data against CRC-8 checksum."""
        return CRC8.calculate(data) == checksum


class CRC16:
    """CRC-16 (CCITT) error detection implementation."""

    POLYNOMIAL = 0x1021
    TABLE = None

    @classmethod
    def _init_table(cls) -> List[int]:
        """Initialize CRC lookup table."""
        if cls.TABLE is not None:
            return cls.TABLE
        cls.TABLE = [0] * 256
        for i in range(256):
            crc = i << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ cls.POLYNOMIAL
                else:
                    crc <<= 1
                crc &= 0xFFFF
            cls.TABLE[i] = crc
        return cls.TABLE

    @staticmethod
    def calculate(data: bytes) -> int:
        """Calculate CRC-16 checksum for data."""
        CRC16._init_table()
        crc = 0xFFFF
        for byte in data:
            crc = ((crc << 8) & 0xFFFF) ^ CRC16.TABLE[((crc >> 8) ^ byte) & 0xFF]
        return crc & 0xFFFF

    @staticmethod
    def verify(data: bytes, checksum: int) -> bool:
        """Verify data against CRC-16 checksum."""
        return CRC16.calculate(data) == checksum


class SpaceWirePacket:
    """
    SpaceWire packet implementation.
    
    SpaceWire is a serial bus standard for spacecraft communications,
    defined by the European Space Agency (ESA).
    """

    PROTOCOL_ID = 0x88B5

    def __init__(
        self,
        src: int = 0x01,
        dst: int = 0x02,
        route: int = 0x00,
        data: bytes = b"",
        packet_type: PacketType = PacketType.DATA,
        priority: PacketPriority = PacketPriority.NORMAL,
    ):
        self.src = src
        self.dst = dst
        self.route = route
        self.data = data
        self.packet_type = packet_type
        self.priority = priority
        self.crc = CRC8.calculate(data)
        self.timestamp = time.time()

    def __repr__(self) -> str:
        return (
            f"SpaceWirePacket(src=0x{self.src:02X}, dst=0x{self.dst:02X}, "
            f"size={len(self.data)} bytes, crc=0x{self.crc:02X})"
        )

    def verify(self) -> bool:
        """Verify packet integrity using CRC-8."""
        return CRC8.verify(self.data, self.crc)

    def simulate_error(self, error_probability: float = 0.1) -> bool:
        """
        Simulate a random transmission error.
        
        Returns True if error was injected.
        """
        if random.random() < error_probability:
            self.crc ^= 0xFF
            return True
        return False

    def to_bytes(self) -> bytes:
        """Serialize packet to bytes."""
        header = bytes([self.src, self.dst, self.route, self.packet_type.value])
        return header + self.data + bytes([self.crc])

    @classmethod
    def from_bytes(cls, data: bytes) -> "SpaceWirePacket":
        """Deserialize packet from bytes."""
        if len(data) < 5:
            raise ValueError("Packet data too short")
        src, dst, route, packet_type = data[:4]
        packet_type = PacketType(packet_type)
        crc = data[-1]
        payload = data[4:-1]
        return cls(src, dst, route, payload, packet_type)


class SpaceFibrePacket(SpaceWirePacket):
    """
    SpaceFibre packet implementation.
    
    SpaceFibre is a high-speed serial bus standard that extends
    SpaceWire with higher rates and quality of service (QoS).
    """

    PROTOCOL_ID = 0x88B6
    NUM_VIRTUAL_CHANNELS = 8

    def __init__(
        self,
        src: int = 0x01,
        dst: int = 0x02,
        route: int = 0x00,
        data: bytes = b"",
        virtual_channel: int = 0,
        sequence_number: int = 0,
        flow_control: bool = False,
        packet_type: PacketType = PacketType.DATA,
        priority: PacketPriority = PacketPriority.NORMAL,
    ):
        super().__init__(src, dst, route, data, packet_type, priority)
        self.virtual_channel = virtual_channel
        self.sequence_number = sequence_number
        self.flow_control = flow_control
        self.crc = CRC16.calculate(data)

    def __repr__(self) -> str:
        return (
            f"SpaceFibrePacket(src=0x{self.src:02X}, dst=0x{self.dst:02X}, "
            f"vc={self.virtual_channel}, seq={self.sequence_number}, "
            f"size={len(self.data)} bytes)"
        )

    def verify(self) -> bool:
        """Verify packet integrity using CRC-16."""
        return CRC16.verify(self.data, self.crc)

    def to_bytes(self) -> bytes:
        """Serialize packet to bytes."""
        header = bytes([
            self.src,
            self.dst,
            self.virtual_channel,
            self.sequence_number,
            0x01 if self.flow_control else 0x00,
        ])
        return header + self.data + bytes([self.crc >> 8, self.crc & 0xFF])


class PacketFactory:
    """Factory for creating different packet types."""

    _packet_id_counter = 0
    _lock = threading.Lock()

    @classmethod
    def create_spacewire(
        cls,
        src: int,
        dst: int,
        data: bytes,
        priority: PacketPriority = PacketPriority.NORMAL,
    ) -> SpaceWirePacket:
        """Create a SpaceWire packet."""
        return SpaceWirePacket(
            src=src,
            dst=dst,
            data=data,
            priority=priority,
        )

    @classmethod
    def create_spacefibre(
        cls,
        src: int,
        dst: int,
        data: bytes,
        virtual_channel: int = 0,
        priority: PacketPriority = PacketPriority.NORMAL,
    ) -> SpaceFibrePacket:
        """Create a SpaceFibre packet."""
        with cls._lock:
            cls._packet_id_counter += 1
            seq_num = cls._packet_id_counter

        return SpaceFibrePacket(
            src=src,
            dst=dst,
            data=data,
            virtual_channel=virtual_channel,
            sequence_number=seq_num,
            priority=priority,
        )

    @classmethod
    def create_batch(
        cls,
        src: int,
        dst: int,
        file_data: bytes,
        chunk_size: int = 1000,
        protocol: str = "spacewire",
        **kwargs,
    ) -> List[SpaceWirePacket]:
        """Create a batch of packets from file data."""
        packets: List[SpaceWirePacket] = []
        num_chunks = len(file_data) // chunk_size + (1 if len(file_data) % chunk_size != 0 else 0)

        for i in range(num_chunks):
            chunk = file_data[i * chunk_size : (i + 1) * chunk_size]
            if protocol == "spacefibre":
                pkt = cls.create_spacefibre(src, dst, chunk, **kwargs)
            else:
                pkt = cls.create_spacewire(src, dst, chunk, **kwargs)
            packets.append(pkt)

        return packets
