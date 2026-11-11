from __future__ import annotations

import json

import networkx as nx
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

PROJECTED_CRS = "EPSG:32645"
PROJECT = Transformer.from_crs("EPSG:4326", PROJECTED_CRS, always_xy=True).transform
SNAP_TOLERANCE_M = 250


def metric_distance(a, b) -> float:
    return transform(PROJECT, Point(a)).distance(transform(PROJECT, Point(b)))


def area_for_point(areas, longitude: float, latitude: float):
    point = Point(longitude, latitude)
    matches = [area for area in areas if shape(json.loads(area["geometry_json"])).covers(point)]
    # Boundaries can belong to two cells. Choose deterministically and disclose boundary semantics.
    return min(matches, key=lambda area: area["id"]) if matches else None


def expanded_edges(roads, chosen_ids):
    by_id = {road["id"]: road for road in roads}
    if any(edge not in by_id for edge in chosen_ids):
        raise ValueError("A selected road edge is outside the pilot graph.")
    segments = {by_id[edge]["segment_id"] for edge in chosen_ids}
    return sorted(road["id"] for road in roads if road["segment_id"] in segments)


def calculate_route(areas, nodes, roads, hazards, start, end):
    if area_for_point(areas, *start) is None or area_for_point(areas, *end) is None:
        return {"status": "outside_pilot", "message": "Both route points must be inside the synthetic study area."}
    exclusions = {edge for hazard in hazards for edge in json.loads(hazard["edge_ids_json"])}
    snap = lambda point: min(nodes, key=lambda node: metric_distance(point, (node["longitude"], node["latitude"])))
    start_node, end_node = snap(start), snap(end)
    snap_distances = [metric_distance(start, (start_node["longitude"], start_node["latitude"])),
                      metric_distance(end, (end_node["longitude"], end_node["latitude"]))]
    if max(snap_distances) > SNAP_TOLERANCE_M:
        return {"status": "unsnappable", "message": "A point is more than 250 m from a mapped accessible node.",
                "snap_distance_m": [round(value, 1) for value in snap_distances]}
    graph = nx.MultiDiGraph()
    graph.add_nodes_from(node["id"] for node in nodes)
    for road in roads:
        if road["id"] not in exclusions:
            graph.add_edge(road["source_node"], road["target_node"], key=road["id"],
                           length=road["length_m"], road=road)
    try:
        path = nx.shortest_path(graph, start_node["id"], end_node["id"], weight="length")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return {"status": "unavailable", "message": "No route avoiding the currently verified hazards could be found.",
                "excluded_edge_ids": sorted(exclusions), "hazard_ids": [hazard["id"] for hazard in hazards]}
    edges = [min(graph.get_edge_data(a, b).values(), key=lambda item: item["length"])["road"]
             for a, b in zip(path, path[1:])]
    assert not exclusions.intersection(road["id"] for road in edges)
    lookup = {node["id"]: node for node in nodes}
    coordinates = [[lookup[node]["longitude"], lookup[node]["latitude"]] for node in path]
    # A same-node route is valid, and GeoJSON LineString needs at least two positions.
    if len(coordinates) == 1:
        coordinates.append(coordinates[0])
    return {"status": "available", "geometry": {"type": "LineString", "coordinates": coordinates},
            "edge_ids": [road["id"] for road in edges], "node_ids": path,
            "distance_m": round(sum(road["length_m"] for road in edges), 1),
            "snap_distance_m": [round(value, 1) for value in snap_distances],
            "excluded_edge_ids": sorted(exclusions), "hazard_ids": [hazard["id"] for hazard in hazards],
            "message": "This suggestion avoids currently verified flooded segments. Other hazards or missing reports may exist.",
            "network_source": "Synthetic directed road fixture; distance cost; pedestrian demonstration only."}
