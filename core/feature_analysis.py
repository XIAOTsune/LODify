import math
from collections import defaultdict
import math


def _uv_edge_boundary(edge, uv_layer, epsilon=1e-5):
    loops = list(edge.link_loops)
    if len(loops) != 2:
        return False

    uv_by_face = []
    for loop in loops:
        try:
            uv_by_face.append({
                loop.vert.index: loop[uv_layer].uv.copy(),
                loop.link_loop_next.vert.index: loop.link_loop_next[uv_layer].uv.copy(),
            })
        except (AttributeError, KeyError, ReferenceError):
            return False

    for vertex_index in uv_by_face[0].keys() & uv_by_face[1].keys():
        if (uv_by_face[0][vertex_index] - uv_by_face[1][vertex_index]).length > epsilon:
            return True
    return False


def score_bmesh_edge(edge, uv_layer, crease_layer, settings):
    """Return a compact feature record, or None when the edge is uninteresting."""
    face_count = len(edge.link_faces)
    if face_count == 0:
        return None

    reasons = []
    hard_protected = face_count != 2
    if face_count == 1:
        reasons.append("boundary")
    elif face_count > 2:
        reasons.append("non_manifold")

    angle = 0.0
    if face_count == 2 and getattr(edge, "is_manifold", False):
        try:
            angle = abs(float(edge.calc_face_angle(0.0)))
        except (AttributeError, ValueError, TypeError, ReferenceError):
            angle = 0.0

    sharp = not bool(getattr(edge, "smooth", True))
    crease = False
    if crease_layer is not None:
        try:
            crease = float(edge[crease_layer]) > 1e-5
        except (KeyError, TypeError, ValueError, ReferenceError):
            crease = False
    seam = bool(getattr(edge, "seam", False))
    uv_boundary = _uv_edge_boundary(edge, uv_layer) if uv_layer is not None else False
    material_boundary = face_count == 2 and (
        edge.link_faces[0].material_index != edge.link_faces[1].material_index
    )

    protection_checks = (
        (sharp, settings.get("protect_sharp", True), "sharp"),
        (crease, settings.get("protect_crease", True), "crease"),
        (uv_boundary, settings.get("protect_uv", True), "uv_boundary"),
        (seam, settings.get("protect_seam", False), "seam"),
        (material_boundary, settings.get("protect_material", True), "material_boundary"),
    )

    protected = hard_protected
    for detected, protect, reason in protection_checks:
        if not detected or not protect:
            continue
        reasons.append(reason)
        protected = True

    threshold = math.radians(float(settings.get("angle_threshold_degrees", 45.0)))
    is_angle_feature = angle >= threshold
    if is_angle_feature:
        reasons.append("dihedral")

    if not protected and not is_angle_feature:
        return None

    score = max(angle / math.pi, 1.0 if protected else 0.0)
    return {
        "edge_index": edge.index,
        "vertices": (edge.verts[0].index, edge.verts[1].index),
        "kind": "protected" if protected else "candidate",
        "score": min(1.0, score),
        "reasons": tuple(reasons),
    }


def trace_edge_paths(edge_records, min_edges=1):
    """Turn an unordered set of edge records into deterministic open paths and loops."""
    records = {record["edge_index"]: record for record in edge_records}
    adjacency = defaultdict(list)
    for edge_index, record in records.items():
        start, end = record["vertices"]
        adjacency[start].append(edge_index)
        adjacency[end].append(edge_index)

    for edge_indices in adjacency.values():
        edge_indices.sort()

    unused = set(records)
    paths = []

    def walk(start_vertex, first_edge):
        edge_indices = []
        vertices = [start_vertex]
        current_vertex = start_vertex
        next_edge = first_edge
        closed = False

        while next_edge in unused:
            unused.remove(next_edge)
            edge_indices.append(next_edge)
            start, end = records[next_edge]["vertices"]
            next_vertex = end if start == current_vertex else start
            vertices.append(next_vertex)

            if next_vertex == start_vertex:
                closed = True
                break
            if len(adjacency[next_vertex]) != 2:
                break

            continuations = [idx for idx in adjacency[next_vertex] if idx in unused]
            if len(continuations) != 1:
                break
            current_vertex = next_vertex
            next_edge = continuations[0]

        return edge_indices, vertices, closed

    for vertex_index in sorted(adjacency):
        if len(adjacency[vertex_index]) == 2:
            continue
        for edge_index in adjacency[vertex_index]:
            if edge_index not in unused:
                continue
            edge_indices, vertices, closed = walk(vertex_index, edge_index)
            if len(edge_indices) >= min_edges:
                paths.append((edge_indices, vertices, closed))

    while unused:
        edge_index = min(unused)
        start_vertex = min(records[edge_index]["vertices"])
        edge_indices, vertices, closed = walk(start_vertex, edge_index)
        if len(edge_indices) >= min_edges:
            paths.append((edge_indices, vertices, closed))

    result = []
    for edge_indices, vertices, closed in paths:
        path_records = [records[index] for index in edge_indices]
        result.append({
            "edge_indices": tuple(edge_indices),
            "vertex_indices": tuple(vertices),
            "closed": closed,
            "feature_score": sum(item["score"] for item in path_records) / len(path_records),
            "reasons": tuple(sorted({reason for item in path_records for reason in item["reasons"]})),
            "branch_points": tuple(sorted(
                vertex for vertex in set(vertices) if len(adjacency[vertex]) > 2
            )),
        })

    result.sort(key=lambda path: path["edge_indices"][0])
    return result
