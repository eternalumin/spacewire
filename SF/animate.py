import pygame
import random
from collections import deque
from topology import get_topology

# Pygame setup
WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (30, 30, 30)
EDGE_COLOR = (200, 200, 200)
FPS = 30

# Load device images
# Load device images and resize them to 50x50 pixels
DEVICE_IMAGES = {
    "Packet": pygame.transform.scale(pygame.image.load("packet.png"), (30, 30)),
    "Node1": pygame.transform.scale(pygame.image.load("obc.png"), (80, 80)),
    "Node2": pygame.transform.scale(pygame.image.load("router.png"), (80, 80)),
    "Node3": pygame.transform.scale(pygame.image.load("camera.png"), (80, 80)),
    "Node4": pygame.transform.scale(pygame.image.load("ssd.png"), (80, 80)),
    "Node5": pygame.transform.scale(pygame.image.load("aocs.png"), (80, 80)),
}


# Node positions
NODES = [
    {"id": "0x001", "pos": (150, 300), "image": "Node1"},
    {"id": "0x002", "pos": (350, 100), "image": "Node2"},
    {"id": "0x003", "pos": (550, 100), "image": "Node3"},
    {"id": "0x004", "pos": (350, 500), "image": "Node4"},
    {"id": "0x005", "pos": (550, 500), "image": "Node5"},
]

# Function to find shortest path using BFS
# Function to find shortest path using BFS
def find_path(src_id, dst_id, edges):
    graph = {node["id"]: [] for node in NODES}
    
    for u, neighbors in edges.items():
        for v in neighbors:
            if isinstance(v, list):  # Ensure v is a string
                v = v[0]
            graph.setdefault(u, []).append(v)
            graph.setdefault(v, []).append(u)  # Ensure bidirectional connectivity

    queue = deque([(src_id, [src_id])])
    visited = set()

    while queue:
        current, path = queue.popleft()
        if current == dst_id:
            return path
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []

# Animate the packet traveling along the path
# Animate the packet traveling along the path
def animate_packet(screen, path):
    if not path:
        return

    packet_img = DEVICE_IMAGES["Packet"]
    node_positions = {node["id"]: node["pos"] for node in NODES}


    for i in range(len(path) - 1):
        src = node_positions[path[i]]
        dst = node_positions[path[i + 1]]
        steps = 30  # Smooth animation steps

        for step in range(steps + 1):
            t = step / steps
            x = (1 - t) * src[0] + t * dst[0]
            y = (1 - t) * src[1] + t * dst[1]

            screen.blit(packet_img, (int(x) - 15, int(y) - 15))  # Center packet
            pygame.display.flip()
            pygame.display.update()  # Force screen update

            pygame.time.delay(20)

# Draw the topology
def draw_topology(screen, src, dst_list):
    node_positions = {node["id"]: node["pos"] for node in NODES}
    edges = get_topology(current_topology, src, dst_list)  # Now it gets values from run_simulation()

    for u, neighbors in edges.items():
        if u not in node_positions:
            continue
        for v in neighbors:
            if isinstance(v, list):
                v = v[0]
            if v not in node_positions:
                continue
            pygame.draw.line(screen, EDGE_COLOR, node_positions[u], node_positions[v], 2)

    for node in NODES:
        screen.blit(DEVICE_IMAGES[node["image"]], (node["pos"][0] - 25, node["pos"][1] - 25))




# Main simulation function
def run_simulation(topology, src, dst_list):
    global current_topology
    current_topology = topology
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"SpaceWire - {topology.capitalize()} Topology")
    clock = pygame.time.Clock()
    running = True

    path = find_path(src, dst_list[0], get_topology(current_topology, src, dst_list))  # Get shortest path

    while running:
        screen.fill(BACKGROUND_COLOR)
        draw_topology(screen, src, dst_list)  # ✅ Fix: Pass src and dst_list
        
        if path:  # Ensure there's a valid path before animating
            animate_packet(screen, path)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        clock.tick(FPS)

    pygame.quit()




# Example usage
