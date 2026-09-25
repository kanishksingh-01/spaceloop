"""
SpaceLoop Entity Relationship Graph Engine
Models marketplace interactions as an attributed heterogeneous graph:
- Nodes: User, Space, Booking, Review, DeviceFingerprint, IPAddress
- Edges: AUTH_ON, HOSTS, BOOKED, REVIEWED, ACCESSED_FROM
Provides:
- Shared infrastructure & collusion detection (Host & Seeker sharing devices/IPs)
- Directed cycle detection (circular booking loops)
- High-degree entity concentration & Sybil ring discovery
- Subgraph extraction for admin visualization
"""
from collections import defaultdict, deque
from typing import Any
from models import db, User, Space, Booking, Review, DeviceSession


class MarketplaceGraph:
    """
    In-memory graph adjacency structure populated dynamically from database entities.
    """
    def __init__(self):
        # Adjacency list: node_id -> set of (neighbor_id, edge_type)
        self.adj = defaultdict(set)
        # Node metadata: node_id -> {type, label, attributes}
        self.nodes = {}

    def add_node(self, node_id: str, node_type: str, label: str = "", **attrs):
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label or node_id,
            **attrs
        }

    def add_edge(self, src: str, dst: str, edge_type: str, **attrs):
        self.adj[src].add((dst, edge_type))
        # Keep reverse edge for bidirectional entity queries
        self.adj[dst].add((src, f"REV_{edge_type}"))

    def neighbors(self, node_id: str, edge_type_filter: str | None = None) -> list[tuple[str, str]]:
        if edge_type_filter:
            return [(nbr, et) for (nbr, et) in self.adj.get(node_id, set()) if et == edge_type_filter]
        return list(self.adj.get(node_id, set()))

    def find_shared_devices_and_ips(self, user_a_id: int, user_b_id: int) -> dict:
        """
        Detects whether two distinct user accounts share device fingerprints or IP addresses.
        """
        node_a = f"user:{user_a_id}"
        node_b = f"user:{user_b_id}"

        devices_a = {nbr for nbr, et in self.adj.get(node_a, set()) if nbr.startswith("device:")}
        devices_b = {nbr for nbr, et in self.adj.get(node_b, set()) if nbr.startswith("device:")}
        shared_devices = list(devices_a.intersection(devices_b))

        ips_a = {nbr for nbr, et in self.adj.get(node_a, set()) if nbr.startswith("ip:")}
        ips_b = {nbr for nbr, et in self.adj.get(node_b, set()) if nbr.startswith("ip:")}
        shared_ips = list(ips_a.intersection(ips_b))

        return {
            "has_shared_infrastructure": bool(shared_devices or shared_ips),
            "shared_devices": shared_devices,
            "shared_ips": shared_ips,
            "shared_device_count": len(shared_devices),
            "shared_ip_count": len(shared_ips)
        }

    def detect_directed_cycles(self, max_depth: int = 4) -> list[list[str]]:
        """
        Detects circular transaction loops among users (e.g. User A -> User B -> User A).
        """
        user_graph = defaultdict(set)
        for node, nbrs in self.adj.items():
            is_user = node.startswith("user:") or node.startswith("user_") or self.nodes.get(node, {}).get("type", "").lower() == "user"
            if is_user:
                for nbr, et in nbrs:
                    if et == "BOOKED_HOST":
                        user_graph[node].add(nbr)

        cycles = []
        visited = set()

        def dfs(start, current, path, depth):
            if depth > max_depth:
                return
            for neighbor in user_graph.get(current, set()):
                if neighbor == start and len(path) >= 2:
                    cycle = list(path) + [start]
                    # Normalize cycle rotation for uniqueness
                    min_idx = cycle.index(min(cycle[:-1]))
                    norm = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                    cycle_key = "->".join(norm)
                    if cycle_key not in visited:
                        visited.add(cycle_key)
                        cycles.append(norm)
                elif neighbor not in path and depth < max_depth:
                    dfs(start, neighbor, path + [neighbor], depth + 1)

        for u in list(user_graph.keys()):
            dfs(u, u, [u], 1)

        return cycles

    def find_multi_account_rings(self, threshold: int = 3) -> list[dict]:
        """
        Finds devices or IPs connected to threshold or more distinct user accounts.
        """
        rings = []
        for node, attrs in self.nodes.items():
            if attrs["type"] in ("device", "ip"):
                linked_users = [nbr for nbr, et in self.adj.get(node, set()) if nbr.startswith("user:")]
                if len(linked_users) >= threshold:
                    rings.append({
                        "infrastructure_node": node,
                        "infrastructure_type": attrs["type"],
                        "linked_user_count": len(linked_users),
                        "linked_users": linked_users
                    })
        return rings

    def extract_subgraph(self, center_node_id: str, hops: int = 2) -> dict:
        """
        Extracts an egocentric subgraph around an entity for frontend visualization.
        """
        sub_nodes = {}
        sub_edges = []
        visited_nodes = {center_node_id}
        queue = deque([(center_node_id, 0)])

        while queue:
            curr, dist = queue.popleft()
            if curr in self.nodes:
                sub_nodes[curr] = self.nodes[curr]

            if dist < hops:
                for nbr, et in self.adj.get(curr, set()):
                    if not et.startswith("REV_"):  # Only record forward edges in edge list
                        sub_edges.append({"source": curr, "target": nbr, "type": et})
                    if nbr not in visited_nodes:
                        visited_nodes.add(nbr)
                        queue.append((nbr, dist + 1))

        return {
            "center": center_node_id,
            "nodes": list(sub_nodes.values()),
            "edges": sub_edges,
            "subgraph_size": {
                "nodes": len(sub_nodes),
                "edges": len(sub_edges)
            }
        }


def build_marketplace_graph(limit_days: int = 60) -> MarketplaceGraph:
    """
    Builds the current marketplace graph from the database.
    """
    graph = MarketplaceGraph()

    # 1. Users
    users = User.query.all()
    for u in users:
        u_node = f"user:{u.id}"
        graph.add_node(
            u_node,
            node_type="user",
            label=u.name,
            role=u.role,
            is_verified=bool(u.is_host_verified or u.is_student_verified or u.is_aadhaar_verified),
            trust_score=u.objective_trust_score
        )

    # 2. Device Sessions
    device_sessions = DeviceSession.query.all()
    for ds in device_sessions:
        u_node = f"user:{ds.user_id}"
        dev_node = f"device:{ds.device_fingerprint[:16]}"
        ip_node = f"ip:{ds.ip_hash[:16]}"

        graph.add_node(dev_node, node_type="device", label=f"Dev-{ds.device_fingerprint[:8]}")
        graph.add_node(ip_node, node_type="ip", label=f"IP-{ds.ip_hash[:8]}")

        graph.add_edge(u_node, dev_node, "AUTH_ON")
        graph.add_edge(u_node, ip_node, "ACCESSED_FROM")

    # 3. Spaces & Listings
    spaces = Space.query.all()
    for s in spaces:
        s_node = f"space:{s.id}"
        u_node = f"user:{s.owner_id}"
        graph.add_node(s_node, node_type="space", label=s.title, category=s.category, price=s.price_hourly)
        graph.add_edge(u_node, s_node, "HOSTS")

    # 4. Bookings
    bookings = Booking.query.all()
    for b in bookings:
        b_node = f"booking:{b.id}"
        renter_node = f"user:{b.renter_id}"
        space_node = f"space:{b.space_id}"

        graph.add_node(b_node, node_type="booking", label=f"Booking #{b.id}", status=b.status, amount=b.total_price)
        graph.add_edge(renter_node, b_node, "CREATED_BOOKING")
        graph.add_edge(b_node, space_node, "RESERVED_SPACE")

        # Direct Host-Seeker relationship edge
        if b.space and b.space.owner_id:
            host_node = f"user:{b.space.owner_id}"
            graph.add_edge(renter_node, host_node, "BOOKED_HOST", booking_id=b.id)

    # 5. Reviews
    reviews = Review.query.all()
    for r in reviews:
        r_node = f"review:{r.id}"
        u_node = f"user:{r.user_id}"
        s_node = f"space:{r.space_id}"

        graph.add_node(r_node, node_type="review", label=f"Rating {r.rating}★", rating=r.rating)
        graph.add_edge(u_node, r_node, "WROTE_REVIEW")
        graph.add_edge(r_node, s_node, "REVIEW_FOR")

    return graph
