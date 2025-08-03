import random
import time
from scapy.all import *
from topology import get_topology
from animate import run_simulation
import json

# Custom SpaceWire-like protocol packet
class SpaceWire(Packet):
    name = "SpaceWire"
    fields_desc = [
        ByteField("src", 0x01),
        ByteField("dst", 0x02),
        ByteField("route", 0x00),
        StrLenField("data", "", length_from=lambda pkt: len(pkt.data)),
        ByteField("crc", 0x00)
    ]

# Metrics
packets_sent = 0
errors_detected = 0
latency_records = []

# CRC-8 Calculation
def crc8(data):
    crc = 0
    for byte in data:
        crc ^= byte
    return crc & 0xFF

# Ensure consistent "0xNNN" format
def format_node_id(n):
    return f"0x{int(n):03d}"

INTERFACE = "Wi-Fi" #nge as needed

def send_file(src, dst, file_path):
    global packets_sent, errors_detected, latency_records
    
    # Open the file and read its content
    with open(file_path, "rb") as file:
        file_data = file.read()

    # Split file data into smaller chunks (e.g., 1000 bytes per packet)
    chunk_size = 1000  # Define a suitable chunk size (can be adjusted)
    num_chunks = len(file_data) // chunk_size + (1 if len(file_data) % chunk_size != 0 else 0)
    
    for i in range(num_chunks):
        chunk = file_data[i * chunk_size : (i + 1) * chunk_size]
        pkt = SpaceWire(src=src, dst=dst, data=chunk, crc=crc8(chunk))

        start_time = time.time()

        if random.random() < 0.2:  # Simulate lower error rate (20%)
            pkt.crc ^= 0xFF  # Introduce a random error in CRC

        # Send the packet
        sendp(Ether(dst="ff:ff:ff:ff:ff:ff", type=0x88B5) / pkt, iface=INTERFACE)
        packets_sent += 1

        # Calculate CRC after sending
        received_crc = crc8(pkt.data)

        if received_crc != pkt.crc:
            errors_detected += 1
            print(f"[ERROR] CRC Mismatch in SpaceFibre packet: {pkt.summary()}")

        end_time = time.time()
        latency_records.append(end_time - start_time)

    print(f"Sent file '{file_path}' in {num_chunks} packets.")


def compute_metrics():
    total_packets = packets_sent
    throughput = packets_sent / sum(latency_records) if latency_records else 0
    avg_latency = sum(latency_records) / len(latency_records) if latency_records else 0
    error_rate = (errors_detected / total_packets) * 100 if total_packets else 0

    print("\n--- Performance Metrics ---")
    print(f"Total Packets Sent: {packets_sent}")
    print(f"Errors Detected: {errors_detected}")
    print(f"Error Rate: {error_rate:.2f}%")
    print(f"Throughput: {throughput:.2f} packets/sec")
    print(f"Avg Latency: {avg_latency:.6f} sec\n")

def send_packets_in_topology(topology_name, *args):
    topology = get_topology(topology_name, *args)
    
    for src, destinations in topology.items():
        for dst in destinations:
            
            send_file(src, dst, file_path)
            time.sleep(0.5)  # Adjust sleep time based on your network conditions


def export_metrics(filename):
    base_power = 10  # mW (baseline power consumption)
    latency_factor = 5000  # power increase per unit of latency

    # Average latency calculation
    avg_latency = sum(latency_records) / len(latency_records) if latency_records else 0
    power_mw = base_power * (1 + latency_factor * avg_latency)  # Precise power consumption model

    metrics = {
        "packets_sent": packets_sent,
        "errors_detected": errors_detected,
        "latency_records": latency_records,
        "throughput": packets_sent / sum(latency_records) if latency_records else 0,
        "avg_latency": avg_latency,
        "error_rate": (errors_detected / packets_sent) * 100 if packets_sent else 0,
        "power_mw": power_mw
    }
    with open(filename, "w") as f:
        json.dump(metrics, f)

if __name__ == "__main__":
    print("Running SpaceWire Simulation with Metrics...")

    devices = [0x01, 0x02, 0x03, 0x04, 0x05]
    topology = "point-to-point"
    src = devices[0]
    dst_list = [devices[2]]
    for i in range(3):
        file_path = r"C:\Users\Dell\Music\100p\SF\aocs.png"  # Raw string

        send_packets_in_topology(topology, src, dst_list[0])
    #run_simulation(topology, format_node_id(src), [format_node_id(d) for d in dst_list])
        compute_metrics()
        export_metrics("spacewire_metrics.json")
