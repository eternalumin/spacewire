"""Unit tests for packet module."""

import pytest
from spacewire.packet import (
    CRC8, CRC16, SpaceWirePacket, SpaceFibrePacket, 
    PacketFactory, PacketPriority, PacketType
)


class TestCRC8:
    """Tests for CRC-8 implementation."""

    def test_crc8_basic(self):
        """Test basic CRC-8 calculation."""
        data = b"Hello, World!"
        crc = CRC8.calculate(data)
        assert isinstance(crc, int)
        assert 0 <= crc <= 255

    def test_crc8_verify_valid(self):
        """Test CRC-8 verification with valid data."""
        data = b"Test data"
        crc = CRC8.calculate(data)
        assert CRC8.verify(data, crc) is True

    def test_crc8_verify_invalid(self):
        """Test CRC-8 verification with corrupted data."""
        data = b"Test data"
        crc = CRC8.calculate(data)
        corrupted = data[:-1] + bytes([(data[-1] + 1) % 256])
        assert CRC8.verify(corrupted, crc) is False

    def test_crc8_empty(self):
        """Test CRC-8 with empty data."""
        crc = CRC8.calculate(b"")
        assert crc == 0


class TestCRC16:
    """Tests for CRC-16 implementation."""

    def test_crc16_basic(self):
        """Test basic CRC-16 calculation."""
        data = b"Hello, World!"
        crc = CRC16.calculate(data)
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF

    def test_crc16_verify_valid(self):
        """Test CRC-16 verification with valid data."""
        data = b"Test data"
        crc = CRC16.calculate(data)
        assert CRC16.verify(data, crc) is True

    def test_crc16_verify_invalid(self):
        """Test CRC-16 verification with corrupted data."""
        data = b"Test data"
        crc = CRC16.calculate(data)
        corrupted = data[:-1] + bytes([(data[-1] + 1) % 256])
        assert CRC16.verify(corrupted, crc) is False


class TestSpaceWirePacket:
    """Tests for SpaceWire packet."""

    def test_create_packet(self):
        """Test packet creation."""
        pkt = SpaceWirePacket(src=0x01, dst=0x02, data=b"test")
        assert pkt.src == 0x01
        assert pkt.dst == 0x02
        assert pkt.data == b"test"
        assert pkt.crc != 0

    def test_packet_verify(self):
        """Test packet verification."""
        pkt = SpaceWirePacket(src=0x01, dst=0x02, data=b"test")
        assert pkt.verify() is True

    def test_packet_verify_corrupted(self):
        """Test packet verification with corruption."""
        pkt = SpaceWirePacket(src=0x01, dst=0x02, data=b"test")
        pkt.crc ^= 0xFF
        assert pkt.verify() is False

    def test_packet_serialize(self):
        """Test packet serialization."""
        pkt = SpaceWirePacket(src=0x01, dst=0x02, data=b"test")
        data = pkt.to_bytes()
        assert len(data) > 4
        assert data[0] == 0x01
        assert data[1] == 0x02

    def test_packet_priority(self):
        """Test packet priority."""
        pkt = SpaceWirePacket(src=0x01, dst=0x02, data=b"test", priority=PacketPriority.HIGH)
        assert pkt.priority == PacketPriority.HIGH

    def test_packet_repr(self):
        """Test packet string representation."""
        pkt = SpaceWirePacket(src=0x01, dst=0x02, data=b"test")
        repr_str = repr(pkt)
        assert "0x01" in repr_str
        assert "0x02" in repr_str


class TestSpaceFibrePacket:
    """Tests for SpaceFibre packet."""

    def test_create_packet(self):
        """Test SpaceFibre packet creation."""
        pkt = SpaceFibrePacket(src=0x01, dst=0x02, data=b"test", virtual_channel=3)
        assert pkt.src == 0x01
        assert pkt.dst == 0x02
        assert pkt.virtual_channel == 3
        assert pkt.sequence_number >= 0

    def test_spacefibre_crc16(self):
        """Test SpaceFibre uses CRC-16."""
        pkt = SpaceFibrePacket(src=0x01, dst=0x02, data=b"test")
        pkt.crc = CRC16.calculate(pkt.data)
        assert pkt.verify() is True


class TestPacketFactory:
    """Tests for packet factory."""

    def test_create_spacewire_batch(self):
        """Test batch packet creation."""
        data = b"A" * 2500
        packets = PacketFactory.create_batch(
            0x01, 0x02, data, chunk_size=1000, protocol="spacewire"
        )
        assert len(packets) == 3

    def test_create_spacefibre_batch(self):
        """Test SpaceFibre batch creation."""
        data = b"B" * 2500
        packets = PacketFactory.create_batch(
            0x01, 0x02, data, chunk_size=1000, protocol="spacefibre", virtual_channel=2
        )
        assert len(packets) == 3
        assert all(p.virtual_channel == 2 for p in packets)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
