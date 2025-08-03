from scapy.all import sniff, Raw
from packet import SpaceWire

# File to save raw bytes
byte_file = "captured_data.bin"

def parse_packet(pkt):
    if SpaceWire in pkt:
        sw = pkt[SpaceWire]
        payload = pkt[Raw].load if Raw in pkt else b""  # Get raw payload (bytes)

        print(f"[RECEIVED]")
        print(f"  Topology      : {sw.topology}")
        print(f"  Source Node   : {sw.src}")
        print(f"  Destination   : {sw.dst}")
        print(f"  CRC (recv)    : {sw.crc}")
        print(f"  Payload       : {payload.decode(errors='ignore') if payload else 'No payload'}")

        # Optional: CRC check
        expected_crc = sum(payload) % 256  # CRC as sum of byte values % 256
        if expected_crc != sw.crc:
            print("  CRC MISMATCH! Possible corruption.")
        else:
            print("  CRC OK.")

        # Save the raw packet or payload bytes to a file
        with open(byte_file, "ab") as f:  # 'ab' to append in binary mode
            f.write(pkt)  # Write the entire packet or just the payload (f.write(payload) for payload only)

def start_sniff(interface):
    print(f"[*] Listening on {interface}...")
    sniff(iface=interface, filter="ether proto 0x88b5", prn=parse_packet, store=False)

if __name__ == "__main__":
    try:
        start_sniff("Ethernet")  # Change to match your actual interface
    except KeyboardInterrupt:
        print("\n[*] Stopping packet capture.")
