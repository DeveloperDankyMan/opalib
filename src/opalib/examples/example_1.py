import opalib.format as format
import opalib.util as util
import opalib.http as http
import opalib.web as web
import opalib.format as F
import opalib.physics as physics
import math

from enum import IntEnum, StrEnum
from .mesh_formats import *

class PType(IntEnum):
    UNKNOWN = 0
    INTERIOR = 1
    MIDEXTERIOR = 2
    EXTERIOR = 3
    REFLEX = 4
    INTER = 5
    ACTION = 6
    GOAL = 7
    BLOCKED = 8

is_reflex = {PType.REFLEX, PType.INTER, PType.ACTION, PType.GOAL}

class Actions(IntEnum):
    walk = 0
    jump = 1

host = "127.0.0.1"
port = 8080

app = web.create_app("TestApp")

@app.get("/")
def index(request: web.Request):    
    return {
        "message": "Test App"
    }


def generate_cconnections(points, surfaces, radius, walkSpeed, gravity, jumpPower):
    """Generate CConnections (edges) between nearby points based on proximity, walkability, and jump capability."""
    cconns = []
    
    if not points:
        return cconns
    
    max_jump_h = physics.jump_max_height(jumpPower, gravity)
    
    # Build connection list between points
    for i, p1 in enumerate(points):
        p1_id = p1.get("id", i)
        p1_v3 = p1.get("v3", (0.0, 0.0, 0.0))
        
        for j, p2 in enumerate(points):
            if i >= j:
                continue
            
            p2_id = p2.get("id", j)
            p2_v3 = p2.get("v3", (0.0, 0.0, 0.0))
            
            # Calculate distance
            dx = p2_v3[0] - p1_v3[0]
            dy = p2_v3[1] - p1_v3[1]
            dz = p2_v3[2] - p1_v3[2]
            horiz = math.sqrt(dx*dx + dy*dy)
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Connect if within reasonable distance (e.g., 2x radius)
            if distance <= radius * 2 and distance > 0:
                if dz > 0 and dz <= max_jump_h and horiz <= radius * 1.5:
                    action = Actions.jump
                else:
                    action = Actions.walk

                # Compute connection indices from geometry
                i1 = 1 if dx > 0 else (-1 if dx < 0 else 0)
                i2 = 1 if dy > 0 else (-1 if dy < 0 else 0)
                j1 = 1 if dz > 0 else (-1 if dz < 0 else 0)
                j2 = min(max(int(round(distance / max(radius, 1e-6))), 0), 255)
                
                # Calculate traversal parameters
                t1, t2 = 0.0, 1.0
                u1, u2 = 0.0, 1.0
                
                # Create bidirectional connections
                cconns.append({
                    "action": int(action),
                    "fromID": p1_id,
                    "toID": p2_id,
                    "i1": i1, "i2": i2,
                    "j1": j1, "j2": j2,
                    "t1": t1, "t2": t2,
                    "u1": u1, "u2": u2
                })
                cconns.append({
                    "action": int(action),
                    "fromID": p2_id,
                    "toID": p1_id,
                    "i1": -i1, "i2": -i2,
                    "j1": -j1, "j2": j2,
                    "t1": t1, "t2": t2,
                    "u1": u1, "u2": u2
                })
    
    return cconns


def generate_connections(points, cconns):
    """Generate semantic Connections (movement types) derived from CConnections."""
    connections = []
    
    if not points or len(points) < 2:
        return connections
    
    # Always expose a walk connection for all reachable points.
    at_map = {}
    to_map = {}
    for i, point in enumerate(points):
        point_id = point.get("id", i)
        at_map[point_id] = True
        to_map[point_id] = True
    
    connections.append({
        "type": "walk",
        "bidirectional": True,
        "at": at_map,
        "to": to_map
    })
    
    jump_at = {}
    jump_to = {}
    for c in cconns:
        if c.get("action") == Actions.jump:
            jump_at[c.get("fromID")] = True
            jump_to[c.get("toID")] = True
    if jump_at or jump_to:
        connections.append({
            "type": "jump",
            "bidirectional": True,
            "at": jump_at,
            "to": jump_to
        })
    
    return connections


def _get_v3(p):
    if isinstance(p, dict):
        return tuple(p.get("v3", (0.0, 0.0, 0.0)))
    return (0.0, 0.0, 0.0)


def _distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def _nearest_neighbors(pt_idx, points, k=2):
    target = _get_v3(points[pt_idx])
    dists = []
    for i, p in enumerate(points):
        if i == pt_idx:
            continue
        dists.append((_distance(target, _get_v3(p)), i))
    dists.sort(key=lambda x: x[0])
    return [i for _, i in dists[:k]]


def _angle_at_point(center_v3, a_v3, b_v3):
    ax = a_v3[0] - center_v3[0]
    ay = a_v3[1] - center_v3[1]
    az = a_v3[2] - center_v3[2]
    bx = b_v3[0] - center_v3[0]
    by = b_v3[1] - center_v3[1]
    bz = b_v3[2] - center_v3[2]
    adotb = ax*bx + ay*by + az*bz
    am = math.sqrt(ax*ax + ay*ay + az*az)
    bm = math.sqrt(bx*bx + by*by + bz*bz)
    if am == 0 or bm == 0:
        return 0.0
    cosang = max(-1.0, min(1.0, adotb / (am * bm)))
    return math.degrees(math.acos(cosang))


def _min_distance_to_ptypes(point_v3, points, ptype_values):
    dist = None
    for p in points:
        try:
            if p.get("ptype") in ptype_values:
                candidate = _get_v3(p)
                d = _distance(point_v3, candidate)
                if dist is None or d < dist:
                    dist = d
        except Exception:
            continue
    return dist if dist is not None else float("inf")


def classify_points(points, surfaces, barriers, radius, height, gravity, jumpPower):
    """Classify `ptype` for each point in-place using several heuristics and physics helpers.

    Rules:
    - BLOCKED if point appears in a barrier or if its z is above reachable jump height + agent height
    - INTERIOR if point appears in a surface or has nearby neighbors (within `radius`)
    - REFLEX if local corner angle is sharp (heuristic)
    - EXTERIOR otherwise
    """
    # build id->index map
    id_to_idx = {}
    for i, p in enumerate(points):
        if isinstance(p, dict):
            pid = p.get("id", i)
        else:
            pid = i
        id_to_idx[pid] = i

    surface_point_ids = set()
    for s in surfaces:
        if isinstance(s, (list, tuple)):
            for item in s:
                if isinstance(item, dict):
                    surface_point_ids.add(item.get("id"))
                else:
                    surface_point_ids.add(item)
        elif isinstance(s, dict):
            # if surface is a struct with list of points in first field
            lst = s.get("points") or s.get("list")
            if isinstance(lst, (list, tuple)):
                for item in lst:
                    surface_point_ids.add(item if not isinstance(item, dict) else item.get("id"))

    barrier_point_ids = set()
    for b in barriers:
        if isinstance(b, (list, tuple)):
            for item in b:
                if isinstance(item, dict):
                    barrier_point_ids.add(item.get("id"))
                else:
                    barrier_point_ids.add(item)
        elif isinstance(b, dict):
            inner = b.get("surface") or b.get("Surface")
            if isinstance(inner, (list, tuple)):
                for item in inner:
                    barrier_point_ids.add(item if not isinstance(item, dict) else item.get("id"))

    max_jump_h = physics.jump_max_height(jumpPower, gravity)

    for i, p in enumerate(points):
        try:
            v3 = _get_v3(p)
            pid = p.get("id", i) if isinstance(p, dict) else i

            # BLOCKED by barrier membership
            if pid in barrier_point_ids:
                p["ptype"] = PType.BLOCKED
                continue

            # BLOCKED if vertical clearance is insufficient (point too high)
            if v3[2] > (max_jump_h + height):
                p["ptype"] = PType.BLOCKED
                continue

            # INTERIOR if in surface list
            if pid in surface_point_ids:
                p["ptype"] = PType.INTERIOR
                continue

            # Nearby neighbors imply interior-ish region
            neighbors = _nearest_neighbors(i, points, k=2)
            near = False
            for ni in neighbors:
                if _distance(v3, _get_v3(points[ni])) <= radius * 1.5:
                    near = True
                    break
            if near:
                p["ptype"] = PType.INTERIOR
                continue

            # Heuristic reflex detection using angle between two nearest neighbors
            if len(neighbors) >= 2:
                a = _get_v3(points[neighbors[0]])
                b = _get_v3(points[neighbors[1]])
                ang = _angle_at_point(v3, a, b)
                # if angle is small (sharp corner) mark as REFLEX
                if ang < 60:
                    p["ptype"] = PType.REFLEX
                    continue

            # Default to EXTERIOR
            p["ptype"] = PType.EXTERIOR
        except Exception:
            try:
                p["ptype"] = PType.UNKNOWN
            except Exception:
                pass

    # Post-process to detect MIDEXTERIOR and INTER points using distance computations.
    interior_threshold = radius * 1.5
    for i, p in enumerate(points):
        try:
            v3 = _get_v3(p)
            cur_ptype = p.get("ptype", PType.UNKNOWN)

            if cur_ptype == PType.EXTERIOR:
                distance_to_interior = _min_distance_to_ptypes(v3, points, {PType.INTERIOR, PType.REFLEX, PType.INTER, PType.GOAL})
                if distance_to_interior <= interior_threshold:
                    p["ptype"] = PType.MIDEXTERIOR
                    continue

            if cur_ptype == PType.INTERIOR:
                distance_to_exterior = _min_distance_to_ptypes(v3, points, {PType.EXTERIOR, PType.MIDEXTERIOR})
                if distance_to_exterior <= interior_threshold:
                    # Use a numeric boundary measure rather than pure adjacency.
                    p["ptype"] = PType.INTER
                    continue
        except Exception:
            try:
                p["ptype"] = PType.UNKNOWN
            except Exception:
                pass


@app.post("/mesh/generate")
def mesh_generate(request: web.Request):

    raw = request.raw_body
    if not raw:
        return {
            "error": "dat has not been given."
        }
    
    decoded = util.decode(raw)
    meshreq, _ = util.load(decoded, 0, F.MeshReq, {})

    params = meshreq.get("params", {})
    incoming_mesh = meshreq.get("mesh", {})

    # radius - Defines the minimum horizontal space the agent needs.
    radius = params.get("radius", 1.0)

    # height - Defines the vertical space the agent requires.
    height = params.get("height", 5.0)

    gravity = params.get("gravity", 196.2)
    jumpPower = params.get("jumpPower", 50)
    walkSpeed = params.get("walkSpeed", 16)

    # Extract geometry from incoming_mesh
    points = incoming_mesh.get("points", [])
    surfaces = incoming_mesh.get("surfaces", [])
    barriers = incoming_mesh.get("barriers", [])

    # Classify points with improved helper that uses physics calculations
    try:
        classify_points(points, surfaces, barriers, radius, height, gravity, jumpPower)
    except Exception:
        # fallback: set unknown
        for p in points:
            try:
                p["ptype"] = PType.UNKNOWN
            except Exception:
                pass

    # Generate connectivity graph
    cconns = generate_cconnections(points, surfaces, radius, walkSpeed, gravity, jumpPower)
    connections = generate_connections(points, cconns)

    # Build complete mesh
    generated_mesh = {
        "Name": incoming_mesh.get("Name", "Generated Mesh"),
        "Visible": incoming_mesh.get("Visible", True),
        "points": points,
        "c_conns": cconns,
        "surfaces": surfaces,
        "barriers": barriers,
        "connections": connections
    }

    data = []
    util.save(data, {
        "mesh": generated_mesh
    }, F.MeshSave, {})

    return data

if __name__ == "__main__":
    app.run(host, port, True)