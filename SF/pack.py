import random
import time
from scapy.all import *
from topology import get_topology
import json

# Custom SpaceFibre-like protocol packet
class SpaceFibre(Packet):
    name = "SpaceFibre"
    fields_desc = [
        ByteField("src", 0x01),
        ByteField("dst", 0x02),
        ByteField("vc", 0x01),
        ByteField("seq_num", 0x00),
        ByteField("flow_control", 0x00),
        StrLenField("data", "", length_from=lambda pkt: len(pkt.data)),
        ByteField("crc", 0x00)
    ]

# Global metrics
packets_sent = 0
errors_detected = 0
latency_records = []
jitter_records = []
packet_loss = 0

# CRC8 calculation
def crc8(data):
    crc = 0
    for byte in data:
        crc ^= byte
    return crc & 0xFF

INTERFACE = "Wi-Fi" #nge to your actual interface

def send_packet(src, dst, file_path):
    global packets_sent, errors_detected, latency_records, jitter_records, packet_loss

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()

        packet_size = 1400
        num_chunks = len(file_data) // packet_size + (1 if len(file_data) % packet_size else 0)

        for chunk_index in range(num_chunks):
            start_index = chunk_index * packet_size
            end_index = start_index + packet_size
            chunk_data = file_data[start_index:end_index]

            seq_num = packets_sent + chunk_index
            flow_control = random.choice([0x00, 0x01])

            # Calculate CRC before intentional error
            calculated_crc = crc8(chunk_data)

            pkt = SpaceFibre(
                src=src,
                dst=dst,
                vc=0x01,
                seq_num=seq_num,
                flow_control=flow_control,
                data=chunk_data,
                crc=calculated_crc
            )

            # Simulate CRC corruption (20% chance)
            if random.random() < 0.2:
                pkt.crc ^= 0xFF

            start_time = time.time()
            sendp(Ether(dst="ff:ff:ff:ff:ff:ff", type=0x88B6) / pkt, iface=INTERFACE, verbose=False)
            end_time = time.time()

            packets_sent += 1

            # Simulate packet loss (5% chance)
            if random.random() < 0.05:
                packet_loss += 1
                print(f"[LOSS] Packet dropped: {pkt.summary()}")
                continue

            received_crc = crc8(pkt.data)
            if received_crc != pkt.crc:
                errors_detected += 1
                print(f"[ERROR] CRC mismatch: {pkt.summary()}")

            latency = end_time - start_time
            latency_records.append(latency)

            if len(latency_records) > 1:
                jitter = abs(latency_records[-1] - latency_records[-2])
                jitter_records.append(jitter)

    except Exception as e:
        print(f"[ERROR] Failed to read and send file: {str(e)}")

def compute_metrics():
    total_packets = packets_sent
    throughput = packets_sent / sum(latency_records) if latency_records else 0
    avg_latency = sum(latency_records) / len(latency_records) if latency_records else 0
    error_rate = (errors_detected / total_packets) * 100 if total_packets else 0
    avg_jitter = sum(jitter_records) / len(jitter_records) if jitter_records else 0
    packet_loss_rate = (packet_loss / total_packets) * 100 if total_packets else 0
    power_mw = sum(latency_records) * 0.5 * 1000  # Hypothetical power model

    print("\n--- SpaceFibre QoS Metrics ---")
    print(f"Packets Sent: {packets_sent}")
    print(f"Errors Detected: {errors_detected}")
    print(f"Error Rate: {error_rate:.2f}%")
    print(f"Throughput: {throughput:.2f} packets/sec")
    print(f"Avg Latency: {avg_latency:.6f} sec")
    print(f"Avg Jitter: {avg_jitter:.6f} sec")
    print(f"Packet Loss Rate: {packet_loss_rate:.2f}%")
    print(f"Estimated Power: {power_mw:.2f} mW")

    return {
        "packets_sent": packets_sent,
        "errors_detected": errors_detected,
        "latency_records": latency_records,
        "jitter_records": jitter_records,
        "packet_loss_rate": packet_loss_rate,
        "throughput": throughput,
        "avg_latency": avg_latency,
        "avg_jitter": avg_jitter,
        "error_rate": error_rate,
        "power_mw": power_mw
    }

def send_packets_in_topology(topology_name, file_path, *args):
    topology = get_topology(topology_name, *args)
    for src, destinations in topology.items():
        for dst in destinations:
            send_packet(src, dst, file_path)
            time.sleep(0.3)

def export_metrics(filename, metrics):
    base_power = 10
    latency_factor = 5000
    avg_latency = sum(latency_records) / len(latency_records) if latency_records else 0
    power_mw = base_power * (1 + latency_factor * avg_latency)
    metrics["power_mw"] = power_mw

    with open(filename, "w") as f:
        json.dump(metrics, f, indent=4)

if __name__ == "__main__":
    devices = [0x01, 0x02, 0x03, 0x04, 0x05]
    topology = "point-to-point"
    src = devices[0]
    dst_list = [devices[2]]
    file_path = r"C:\Users\Dell\Music\100p\SF\aocs.png"

    send_packets_in_topology(topology, file_path, src, dst_list[0])

    # Optional single test packet
    test_pkt = SpaceFibre(src=0x01, dst=0x02, data=b"test", crc=crc8(b"test"))
    sendp(Ether(dst="ff:ff:ff:ff:ff:ff", type=0x88B6) / test_pkt, iface=INTERFACE, verbose=False)

    # Compute and export metrics
    metrics = compute_metrics()
    export_metrics("spacefibre_qos_metrics.json", metrics)
