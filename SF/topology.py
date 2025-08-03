# topologies.py - Defines different SpaceWire network topologies

def star_topology(hub, devices):
    """Creates a star topology where the hub device connects to all others."""
    if len(devices) < 1:
        raise ValueError("Star topology requires at least 1 connected device.")
    return {hub: devices}

def ring_topology(start_device, devices):
    """Creates a ring topology where each device connects to the next in a loop."""
    if len(devices) < 1:
        raise ValueError("Ring topology requires at least 1 additional device.")
    ordered_devices = [start_device] + devices
    return {ordered_devices[i]: [ordered_devices[(i + 1) % len(ordered_devices)]] for i in range(len(ordered_devices))}

def mesh_topology(devices):
    """Creates a mesh topology where every device connects to every other device."""
    if len(devices) < 2:
        raise ValueError("Mesh topology requires at least 2 devices.")
    return {dev: [d for d in devices if d != dev] for dev in devices}

def tree_topology(root, children):
    """Creates a tree topology where the root device connects to child devices."""
    if len(children) < 1:
        raise ValueError("Tree topology requires at least 1 child device.")
    tree = {root: children}
    return tree

def point_to_point_topology(src, dst):
    """Creates a point-to-point topology between two devices."""
    return {src: [dst]}

def get_topology(topology_name, *args):
    """
    Returns the topology map based on the selected topology_name and provided devices.
    """
    topology_functions = {
        "star": star_topology,
        "ring": ring_topology,
        "mesh": mesh_topology,
        "tree": tree_topology,
        "point-to-point": point_to_point_topology,
    }
    
    if topology_name not in topology_functions:
        raise ValueError(f"Invalid topology name: {topology_name}")
    
    return topology_functions[topology_name](*args)
