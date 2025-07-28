"""
Generate 1‑metre‑interval lat/lon/elevation CSV along an OpenRouteService route.

Requires:
  pip install openrouteservice shapely pyproj scipy geopy pandas folium

Usage (command line):
  $ python generate_route_csv.py --out route.csv --html route.html \
        --api-key YOUR_ORS_KEY

The script will read the way‑points hard‑coded in WAYPOINTS, query
OpenRouteService with elevation, interpolate the geometry every metre,
attach the nearest elevation value, write a CSV, and optionally save an
interactive Folium map.
"""
import argparse
import csv
import math
import os
from pathlib import Path
from dotenv import load_dotenv

import folium
import numpy as np
import openrouteservice
from geopy.distance import geodesic
from openrouteservice import convert
from pyproj import CRS, Transformer
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from shapely.ops import transform as shp_transform

# ----------------------------- CONFIG ---------------------------------------
# List of way‑points in order (name, lat, lon)
WAYPOINTS = [
    ("Start", -12.463056, 130.837806),
    ("Driver_change", -13.630916, 131.630864),
    ("Cp1", -14.48134, 132.325095),
    ("Cp2", -16.679795, 133.412181),
    ("Cp3", -19.657727, 134.188373),
    ("Cp4", -21.530979, 133.888904),
    ("Cp5", -23.708827, 133.875458),
    ("Cp6", -25.19932, 133.198568),
    ("Cp7", -29.017583, 134.754621),
    ("Cp8", -30.970423, 135.750484),
    ("Cp9", -32.494147, 137.771563),
    ("Finish", -34.931087, 138.620964),
]
INTERVAL_M = 100.0  # spacing between points along the route
# ----------------------------------------------------------------------------

def build_client(api_key: str) -> openrouteservice.Client:
    """Return an ORS client instance."""
    return openrouteservice.Client(key=api_key)


def get_route(coords, client):
    """Call ORS Directions API with elevation and return list of (lon, lat, elev)."""
    res = client.directions(coords, format="geojson", elevation=True)
    return res["features"][0]["geometry"]["coordinates"]  # [[lon, lat, elev], ...]


def get_utm_crs(lon, lat):
    """Return a suitable UTM CRS for the given point (lon, lat)."""
    zone = int((lon + 180) // 6 + 1)
    south = lat < 0
    epsg = 32700 + zone if south else 32600 + zone
    return CRS.from_epsg(epsg)


def interpolate_points(coords3, interval_m=1.0):
    """Return list of (distance_m, lon, lat) interpolated every interval_m."""
    # Determine projection based on first point
    first_lon, first_lat, _ = coords3[0]
    utm_crs = get_utm_crs(first_lon, first_lat)
    to_utm = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True).transform
    to_wgs = Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True).transform

    line = LineString([to_utm(lon, lat) for lon, lat, *_ in coords3])
    total_len = line.length
    num_points = math.floor(total_len / interval_m) + 1

    pts = []
    for i in range(num_points):
        dist = i * interval_m
        p_utm = line.interpolate(dist)
        lon, lat = to_wgs(p_utm.x, p_utm.y)
        pts.append((dist, lon, lat))
    return pts


def attach_elevation(points, coords3):
    """Attach elevation to each (dist, lon, lat) by nearest neighbor."""
    base_xy = np.array([(lon, lat) for lon, lat, _ in coords3])
    elevs = np.array([e for _, _, e in coords3])
    tree = cKDTree(base_xy)
    out = []
    for dist, lon, lat in points:
        _, idx = tree.query([lon, lat])
        out.append((dist, lat, lon, float(elevs[idx])))
    return out


def write_csv(rows, out_path):
    out_path = Path(out_path)
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["distance_m", "latitude", "longitude", "elevation_m"])
        writer.writerows(rows)
    print(f"CSV written to {out_path}")


def create_map(rows, out_html):
    # Center map at halfway point
    mid = rows[len(rows) // 2]
    m = folium.Map(location=[mid[1], mid[2]], zoom_start=5)

    # Add original waypoints
    for name, lat, lon in WAYPOINTS:
        folium.Marker([lat, lon], popup=name).add_to(m)

    # Polyline of route (light blue)
    folium.PolyLine([(r[1], r[2]) for r in rows], color="blue", weight=3, opacity=0.7).add_to(m)

    m.save(out_html)
    print(f"Folium map saved to {out_html}")


def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Generate high‑resolution route CSV with ORS and Elevation.")
    parser.add_argument("--api-key", default=os.getenv("ORS_API_KEY"), help="OpenRouteService API Key")
    parser.add_argument("--out", default="route.csv", help="Output CSV path")
    parser.add_argument("--html", default=None, help="Optional output HTML map path")
    parser.add_argument("--interval", type=float, default=INTERVAL_M, help="Point spacing in metres (default 1)")
    args = parser.parse_args()

    if not args.api_key:
        raise ValueError("API key must be provided via --api-key or ORS_API_KEY env")

    client = build_client(args.api_key)

    coords = [(lon, lat) for _, lat, lon in WAYPOINTS]
    coords3 = get_route(coords, client)

    points = interpolate_points(coords3, interval_m=args.interval)
    rows = attach_elevation(points, coords3)

    write_csv(rows, args.out)

    if args.html:
        create_map(rows, args.html)


if __name__ == "__main__":
    main()

