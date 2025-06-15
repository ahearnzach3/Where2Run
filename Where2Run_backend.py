# Where2Run_backend.py

# 📦 Imports and API Setup
import openrouteservice
import folium
import gpxpy
import gpxpy.gpx
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
# from IPython.display import display -Presence of this code breaks the Streamlit app
import numpy as np
import pandas as pd
import math
import time
import random
from geopy.exc import GeocoderTimedOut
import streamlit as st
import requests
import hashlib
import json
import os


OVERPASS_CACHE_DIR = "cache/overpass"
os.makedirs(OVERPASS_CACHE_DIR, exist_ok=True)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter"
]

def _hash_query(query):
    return hashlib.md5(query.encode('utf-8')).hexdigest()

def run_overpass_query(query, cache_minutes=60):
    cache_key = _hash_query(query)
    cache_path = os.path.join(OVERPASS_CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < cache_minutes * 60):
        with open(cache_path, "r") as f:
            return json.load(f)
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = requests.get(endpoint, params={"data": query}, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            with open(cache_path, "w") as f:
                json.dump(result, f)
            return result
        except Exception as e:
            print(f"Overpass API failed at {endpoint}: {e}")
    return None

def has_matching_environment(lat, lon, mode="suburban", radius=300):
    tag_templates = {
        "trail": [
            'way["highway"~"path|footway|bridleway"](around:{radius},{lat},{lon});',
            'way["surface"~"dirt|gravel|unpaved"](around:{radius},{lat},{lon});',
            'way["leisure"="park"](around:{radius},{lat},{lon});'
        ],
        "suburban": ['way["highway"="residential"](around:{radius},{lat},{lon});'],
        "urban": ['way["highway"~"primary|secondary|tertiary"](around:{radius},{lat},{lon});'],
        "scenic": [
            'way["leisure"="park"](around:{radius},{lat},{lon});',
            'way["natural"~"wood|water"](around:{radius},{lat},{lon});',
            'way["tourism"~"viewpoint"](around:{radius},{lat},{lon});'
        ],
        "shaded": [
            'way["natural"="wood"](around:{radius},{lat},{lon});',
            'way["landuse"="forest"](around:{radius},{lat},{lon});'
        ]
    }
    tags = "\n".join(tag_templates.get(mode.lower(), [])).format(lat=lat, lon=lon, radius=radius)
    query = f"[out:json][timeout:25];({tags});out center;"
    result = run_overpass_query(query)
    return bool(result and result.get("elements"))

def try_route_with_fallback(route_fn, *args, route_environment="Trail", **kwargs):
    lat, lon = kwargs.get("start_coords", (None, None))
    if route_environment.lower() == "trail":
        profile = "foot-hiking" if has_matching_environment(lat, lon, mode="trail") else "foot-walking"
    elif route_environment.lower() == "suburban":
        profile = "foot-walking" if has_matching_environment(lat, lon, mode="suburban") else "foot-walking"
    elif route_environment.lower() == "urban":
        profile = "foot-walking" if has_matching_environment(lat, lon, mode="urban") else "foot-walking"
    elif route_environment.lower() == "scenic":
        profile = "foot-hiking" if has_matching_environment(lat, lon, mode="scenic") else "foot-walking"
    elif route_environment.lower() == "shaded":
        profile = "foot-hiking" if has_matching_environment(lat, lon, mode="shaded") else "foot-walking"
    else:
        profile = "foot-walking"

    try:
        return route_fn(*args, profile=profile, **kwargs)
    except Exception as e:
        print(f"Routing failed with profile={profile}, retrying with foot-walking. Error: {e}")
        return route_fn(*args, profile="foot-walking", **kwargs)




# 🔑 OpenRouteService API
API_KEY = st.secrets["ORS_API_KEY"]
client = openrouteservice.Client(key=API_KEY)

# Mapbox Token for Address Autocompletion
MAPBOX_TOKEN = st.secrets["MAPBOX_TOKEN"]

def mapbox_autocomplete(query):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    params = {
        "access_token": MAPBOX_TOKEN,
        "autocomplete": "true",
        "limit": 5
    }
    resp = requests.get(url, params=params)
    if resp.ok:
        return [feature["place_name"] for feature in resp.json().get("features", [])]
    return []

typed = st.text_input("Start typing your location")
suggestions = mapbox_autocomplete(typed) if typed else []
selected = st.selectbox("Choose a location", suggestions) if suggestions else None

if selected:
    st.write("✅ Selected:", selected)

def get_coords_from_place_name(place_name):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{place_name}.json"
    params = {"access_token": st.secrets["MAPBOX_TOKEN"], "limit": 1}
    resp = requests.get(url, params=params)
    features = resp.json().get("features", [])
    if features:
        lon, lat = features[0]["center"]
        return lat, lon
    return None

# ⌨️ Start Location Autocomplete
def search_places(query):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    params = {
        "access_token": st.secrets["MAPBOX_TOKEN"],
        "autocomplete": "true",
        "limit": 5
    }
    resp = requests.get(url, params=params)
    results = resp.json().get("features", []) if resp.ok else []

    # ✅ This format shows only the name in UI but returns lat/lon
    return [(f["place_name"], tuple(f["center"][::-1])) for f in results]

# 📄 Load Bridges Preset CSV
bridges_preset = pd.read_csv("Preset Routes/bridges_preset_route.csv")
bridges_route_coords = list(zip(bridges_preset["Latitude"], bridges_preset["Longitude"]))

# 🌍 Geocoder
def get_coordinates(address):
    geolocator = Nominatim(user_agent="where2run_geocoder", timeout=5)
    for _ in range(3):
        try:
            location = geolocator.geocode(address)
            if location:
                return (location.latitude, location.longitude)
        except GeocoderTimedOut:
            print("⚠️ Geocoder timed out, retrying...")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Geocoder error: {e}")
            time.sleep(2)
    print("❌ Could not geocode location.")
    return None

# 📏 Route Distance Calculator
def calculate_route_distance(coords):
    total_distance = 0
    for i in range(len(coords) - 1):
        total_distance += geodesic(coords[i], coords[i + 1]).meters
    return total_distance

def generate_loop_route_with_preset_retry(start_coords, distance_miles, bridges_coords=None, max_attempts=8, profile="foot-walking", route_environment=None):
    if route_environment:
        def inner(profile, **_):  # ✅ Handles dynamic profile + extra kwargs
            return generate_loop_route_with_preset_retry(
                start_coords=start_coords,
                distance_miles=distance_miles,
                bridges_coords=bridges_coords,
                max_attempts=max_attempts,
                profile=profile
            )
        return try_route_with_fallback(inner, start_coords=start_coords, route_environment=route_environment)


    # Proceed with original routing logic using provided profile
    original_target_meters = distance_miles * 1609.34
    allowed_range = (original_target_meters - 1207, original_target_meters + 1207)
    reduction_factor = 0.85
    attempt = 0

    while attempt < max_attempts:
        try:
            route_coords = []
            bridges_distance_m = 0

            if bridges_coords:
                print("✅ Including Bridges preset segment.")
                bridges_distance_m = calculate_route_distance(bridges_coords)
                print(f"🔍 Bridges segment distance: {bridges_distance_m / 1609:.2f} miles")

                if start_coords != bridges_coords[0]:
                    print("🔄 Routing to preset start...")
                    to_bridges = client.directions(
                        coordinates=[(start_coords[1], start_coords[0]), (bridges_coords[0][1], bridges_coords[0][0])],
                        profile=profile, format="geojson"
                    )
                    to_bridges_coords = [(pt[1], pt[0]) for pt in to_bridges["features"][0]["geometry"]["coordinates"]]
                    route_coords += to_bridges_coords

                route_coords += bridges_coords

            current_dist_m = calculate_route_distance(route_coords)
            adjusted_remaining = max(0, (original_target_meters - current_dist_m) * reduction_factor)
            print(f"🕕 Requesting round trip of ~{adjusted_remaining / 1609:.2f} miles")

            origin = route_coords[-1] if route_coords else start_coords
            num_points = max(10, min(int(adjusted_remaining / 500), 40))

            round_trip = client.directions(
                coordinates=[(origin[1], origin[0])],
                profile=profile,
                format="geojson",
                options={
                    "round_trip": {
                        "length": adjusted_remaining,
                        "points": num_points,
                        "seed": random.randint(0, 10000)
                    }
                }
            )
            round_trip_coords = [(pt[1], pt[0]) for pt in round_trip["features"][0]["geometry"]["coordinates"]]
            route_coords += round_trip_coords

            total_meters = calculate_route_distance(route_coords)
            print(f"🕕 Total final route distance: {total_meters / 1609:.2f} miles")

            if allowed_range[0] <= total_meters <= allowed_range[1]:
                print("🌟 Route distance within acceptable range.")
                return route_coords
            else:
                print(f"⚠️ Distance out of range: Retrying... ({total_meters / 1609:.2f} mi)")
                reduction_factor -= 0.05
                attempt += 1

        except Exception as e:
            print(f"❌ Error generating loop route (Attempt {attempt + 1}):", e)
            attempt += 1

    print("⚠️ Returning best-effort route despite missed margin.")
    return route_coords if route_coords else None


# 🚩 Loop-with-Destination v3 — Smart Loop + Destination + Return
def generate_loop_with_included_destination_v3(start_coords, target_miles, dest_coords, bridges_coords=None, max_attempts=8, profile="foot-walking", route_environment=None):
    if route_environment:
        def inner(profile, **_):
            return generate_loop_with_included_destination_v3(
                start_coords=start_coords,
                target_miles=target_miles,
                dest_coords=dest_coords,
                bridges_coords=bridges_coords,
                max_attempts=max_attempts,
                profile=profile
            )
        return try_route_with_fallback(inner, start_coords=start_coords, route_environment=route_environment)

    # Proceed with original routing logic using provided profile
    target_total_meters = target_miles * 1609.34
    allowed_range = (target_total_meters - 1207, target_total_meters + 1207)
    reduction_factor = 0.85
    attempt = 0

    # Pre-calculate Destination → Start distance (for budget)
    back_route = client.directions(
        coordinates=[(dest_coords[1], dest_coords[0]), (start_coords[1], start_coords[0])],
        profile=profile,
        format="geojson"
    )
    back_coords = [(pt[1], pt[0]) for pt in back_route["features"][0]["geometry"]["coordinates"]]
    back_meters = calculate_route_distance(back_coords)

    best_coords = None
    best_total_meters = float("inf")

    while attempt < max_attempts:
        try:
            print(f"🕕 Attempt {attempt+1}: Requesting loop via destination (~{target_miles:.2f} mi budget)")

            loop_budget_meters = max(target_total_meters - back_meters - 500, 500)

            # Starting route
            loop_coords = []
            if bridges_coords:
                print("✅ Including Bridges preset.")
                to_bridges = client.directions(
                    coordinates=[(start_coords[1], start_coords[0]), (bridges_coords[0][1], bridges_coords[0][0])],
                    profile=profile, format="geojson"
                )
                to_bridges_coords = [(pt[1], pt[0]) for pt in to_bridges["features"][0]["geometry"]["coordinates"]]
                loop_coords += to_bridges_coords
                loop_coords += bridges_coords
                origin_coords = loop_coords[-1]
            else:
                origin_coords = start_coords

            # Creative loop
            round_trip = client.directions(
                coordinates=[(origin_coords[1], origin_coords[0])],
                profile=profile, format="geojson",
                options={
                    "round_trip": {
                        "length": loop_budget_meters,
                        "points": 12,
                        "seed": random.randint(0, 10000)
                    }
                }
            )
            loop_only_coords = [(pt[1], pt[0]) for pt in round_trip["features"][0]["geometry"]["coordinates"]]

            # Midpoint to force passing through
            mid_lat = (loop_only_coords[-1][0] + dest_coords[0]) / 2
            mid_lon = (loop_only_coords[-1][1] + dest_coords[1]) / 2
            via_point = (mid_lat, mid_lon)

            # Route: loop → via → destination
            to_dest_route = client.directions(
                coordinates=[
                    (loop_only_coords[-1][1], loop_only_coords[-1][0]),
                    (via_point[1], via_point[0]),
                    (dest_coords[1], dest_coords[0])
                ],
                profile=profile, format="geojson"
            )
            to_dest_coords = [(pt[1], pt[0]) for pt in to_dest_route["features"][0]["geometry"]["coordinates"]]
            to_dest_meters = calculate_route_distance(to_dest_coords)

            # Combine full route
            full_coords = loop_coords + loop_only_coords + to_dest_coords + back_coords
            total_meters = calculate_route_distance(full_coords)

            print(f"📏 Full distance: {total_meters / 1609.34:.2f} mi")

            # Distance validation
            if allowed_range[0] <= total_meters <= allowed_range[1]:
                print("✅ Distance within range — returning route.")
                return full_coords

            # Track best attempt
            if abs(total_meters - target_total_meters) < abs(best_total_meters - target_total_meters):
                best_coords = full_coords
                best_total_meters = total_meters

            reduction_factor -= 0.05
            target_total_meters = max(target_total_meters * reduction_factor, 3200)
            attempt += 1

        except Exception as e:
            print(f"❌ Error in attempt {attempt+1}:", e)
            attempt += 1

    print("⚠️ Returning best-effort route.")
    return best_coords if best_coords else None



# 🚩 Out-and-Back with Forced Directional Waypoint (Midpoint Waypoint Method)
def generate_out_and_back_directional_route(start_coords, distance_miles, direction, max_attempts=5, profile="foot-walking", route_environment=None):
    import math
    import time
    import random

    if route_environment:
        def inner(profile, **_):
            return generate_out_and_back_directional_route(
                start_coords=start_coords,
                distance_miles=distance_miles,
                direction=direction,
                max_attempts=max_attempts,
                profile=profile
            )
        return try_route_with_fallback(inner, start_coords=start_coords, route_environment=route_environment)

    # Proceed with original routing logic using provided profile
    target_total_meters = distance_miles * 1609.34
    half_meters = target_total_meters / 2
    allowed_range = (target_total_meters - 1207, target_total_meters + 1207)
    attempt = 0

    heading_angles = {"n": 0, "e": 90, "s": 180, "w": 270}
    heading_deg_base = heading_angles.get(direction.lower(), None)
    if heading_deg_base is None:
        print("❌ Invalid direction — must be N/S/E/W.")
        return None

    print(f"🧭 Target direction → {direction.upper()} ({heading_deg_base}° ± cone)")

    best_coords = None
    best_total_meters = None

    while attempt < max_attempts:
        try:
            jitter_deg = random.uniform(-15, 15)
            heading_deg = (heading_deg_base + jitter_deg) % 360

            print(f"🔄 Attempt {attempt+1}: Forcing midpoint at ~{half_meters / 1609:.2f} miles, heading {heading_deg:.1f}°.")

            angle_rad = math.radians(heading_deg)
            dx = half_meters * math.sin(angle_rad)
            dy = half_meters * math.cos(angle_rad)

            delta_lat = (dy / 111320)
            delta_lon = (dx / (40075000 * math.cos(math.radians(start_coords[0])) / 360))

            midpoint = (start_coords[0] + delta_lat, start_coords[1] + delta_lon)
            print(f"📍 Midpoint forced at approx {midpoint}")

            # Path: start → midpoint → start
            route = client.directions(
                coordinates=[
                    (start_coords[1], start_coords[0]),
                    (midpoint[1], midpoint[0]),
                    (start_coords[1], start_coords[0])
                ],
                profile=profile,
                format="geojson"
            )
            coords = [(pt[1], pt[0]) for pt in route["features"][0]["geometry"]["coordinates"]]

            total_meters = calculate_route_distance(coords)
            total_miles = total_meters / 1609.34
            print(f"📏 Total out-and-back route distance: {total_miles:.2f} miles")

            if allowed_range[0] <= total_meters <= allowed_range[1]:
                print("🌟 Out-and-back route distance within acceptable range → returning this route.")
                return coords

            if best_coords is None or abs(total_meters - target_total_meters) < abs(best_total_meters - target_total_meters if best_total_meters else float('inf')):
                best_coords = coords
                best_total_meters = total_meters

            half_meters = max(half_meters * 0.95, 800)
            attempt += 1
            time.sleep(0.3)

        except Exception as e:
            print("❌ Error generating directional Out-and-Back:", e)
            attempt += 1

    print("⚠️ Returning best-effort Out-and-Back route despite missed margin.")
    if best_coords:
        print(f"⚠️ Best effort route distance: {best_total_meters / 1609.34:.2f} miles")
    return best_coords if best_coords else None


# 🚩 Destination Route Generator
def generate_destination_route(start_coords, dest_coords):
    try:
        route = client.directions(
            coordinates=[(start_coords[1], start_coords[0]), (dest_coords[1], dest_coords[0])],
            profile="foot-walking", format="geojson"
        )
        coords = [(pt[1], pt[0]) for pt in route["features"][0]["geometry"]["coordinates"]]
        total_meters = calculate_route_distance(coords)
        print(f"📏 Estimated one-way distance: {total_meters / 1609:.2f} miles")
        return coords, total_meters / 1609.34
    except Exception as e:
        print("❌ Error generating destination route:", e)
        return None, 0

# 🚩 Round Trip Destination Route
def generate_destination_round_trip(start_coords, dest_coords):
    try:
        route = client.directions(
            coordinates=[(start_coords[1], start_coords[0]), (dest_coords[1], dest_coords[0]), (start_coords[1], start_coords[0])],
            profile="foot-walking", format="geojson"
        )
        coords = [(pt[1], pt[0]) for pt in route["features"][0]["geometry"]["coordinates"]]
        total_meters = calculate_route_distance(coords)
        print(f"📏 Estimated round-trip distance: {total_meters / 1609:.2f} miles")
        return coords
    except Exception as e:
        print("❌ Error generating round-trip destination route:", e)
        return None

# 🚩 Improved Destination Extension Route with Retry + Margin + Detailed Distance Print
def generate_extended_destination_route(start_coords, dest_coords, target_miles, max_attempts=5):
    target_total_meters = target_miles * 1609.34
    allowed_range = (target_total_meters - 1207, target_total_meters + 1207)
    attempt = 0
    reduction_factor = 0.85  # same starting factor as loop routes

    # Calculate one-way distance first
    to_dest_route = client.directions(
        coordinates=[(start_coords[1], start_coords[0]), (dest_coords[1], dest_coords[0])],
        profile="foot-walking",
        format="geojson"
    )
    to_dest_coords = [(pt[1], pt[0]) for pt in to_dest_route["features"][0]["geometry"]["coordinates"]]
    to_dest_meters = calculate_route_distance(to_dest_coords)

    loop_length_meters = max((target_total_meters - to_dest_meters), 500)

    best_coords = None
    best_total_meters = 0

    while attempt < max_attempts:
        try:
            print(f"🔄 Attempt {attempt+1}: Generating loop of ~{loop_length_meters / 1609:.2f} miles at start, then to destination.")

            # Generate loop first
            round_trip = client.directions(
                coordinates=[(start_coords[1], start_coords[0])],
                profile="foot-walking",
                format="geojson",
                options={
                    "round_trip": {
                        "length": loop_length_meters,
                        "points": 20,
                        "seed": random.randint(0, 10000)
                    }
                }
            )
            loop_coords = [(pt[1], pt[0]) for pt in round_trip["features"][0]["geometry"]["coordinates"]]

            # Combine full route
            full_coords = loop_coords + to_dest_coords
            total_meters = calculate_route_distance(full_coords)
            total_miles = total_meters / 1609.34

            print(f"📏 Total extended loop segment distance: {calculate_route_distance(loop_coords)/1609.34:.2f} miles")
            print(f"📏 To-destination segment distance: {to_dest_meters/1609.34:.2f} miles")
            print(f"📏 Total route distance: {total_miles:.2f} miles")

            # Check if within margin
            if allowed_range[0] <= total_meters <= allowed_range[1]:
                print("🌟 Extended route distance within acceptable range.")
                return full_coords

            # Save best attempt so far
            if best_coords is None or abs(total_meters - target_total_meters) < abs(best_total_meters - target_total_meters):
                best_coords = full_coords
                best_total_meters = total_meters

            # Adjust for next attempt
            reduction_factor -= 0.05
            loop_length_meters = max(loop_length_meters * reduction_factor, 500)
            attempt += 1

        except Exception as e:
            print("❌ Error generating extended destination route:", e)
            attempt += 1

    print("⚠️ Returning best-effort extended route despite missed margin.")
    return best_coords if best_coords else None



# ⬆️ Elevation Data Fetcher
def get_elevation_for_coords(coords):
    try:
        if not coords:
            return None
        ors_coords = [(lon, lat) for lat, lon in coords]
        elevation_data = client.elevation_line(geometry=ors_coords, format_in="polyline")
        return elevation_data
    except Exception as e:
        print("❌ Elevation fetch error:", e)
        return None

# ⬆️⬇️ Ascent & Descent Calculator (returns feet)
def calculate_ascent_descent(elevation_data):
    if not elevation_data or "geometry" not in elevation_data:
        return 0, 0
    elevations = [pt[2] for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    ascent = sum(max(0, elevations[i + 1] - elevations[i]) for i in range(len(elevations) - 1))
    descent = sum(max(0, elevations[i] - elevations[i + 1]) for i in range(len(elevations) - 1))
    ascent_ft = ascent * 3.28084
    descent_ft = descent * 3.28084
    return ascent_ft, descent_ft

# 🔍 Elevation-Colored Route Map + Legend
def plot_route_with_elevation(coords, elevation_data):
    if not coords or not elevation_data:
        return None

    elevations = [pt[2] for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    min_elev, max_elev = min(elevations), max(elevations)
    color_scale = np.interp(elevations, [min_elev, max_elev], [0, 1])

    def get_color(val):
        return f"#{int(255 * (1 - val)):02X}{int(255 * val):02X}AA"

    m = folium.Map(location=coords[0], zoom_start=13)

    for i in range(len(coords) - 1):
        folium.PolyLine([coords[i], coords[i + 1]],
                        color=get_color(color_scale[i]), weight=5).add_to(m)

    # Mile markers
    total_dist = 0
    mile = 1
    for i in range(1, len(coords)):
        seg_dist = geodesic(coords[i - 1], coords[i]).miles
        total_dist += seg_dist
        if total_dist >= mile:
            folium.Marker(
                coords[i],
                icon=folium.DivIcon(html=f"""
                    <div style=\"background:blue;color:white;border-radius:50%;width:30px;height:30px;
                    display:flex;align-items:center;justify-content:center;font-weight:bold;\">
                    {mile}</div>""")
            ).add_to(m)
            mile += 1

    folium.Marker(coords[0], popup="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(coords[-1], popup="End", icon=folium.Icon(color="red")).add_to(m)

    # Color Legend
    legend_html = '''
     <div style="
     position: fixed; 
     bottom: 50px; left: 50px; width: 180px; height: 120px; 
     background-color: white; 
     border:2px solid grey; z-index:9999; font-size:14px;
     padding: 10px;">
     <b>Elevation Legend</b><br>
     <i style="background:#FF00AA;width:18px;height:10px;display:inline-block;"></i> High elevation<br>
     <i style="background:#AAFF00;width:18px;height:10px;display:inline-block;"></i> Mid elevation<br>
     <i style="background:#00FFAA;width:18px;height:10px;display:inline-block;"></i> Low elevation
     </div>
     '''

    m.get_root().html.add_child(folium.Element(legend_html))

    return m

# 📈 Elevation Area Chart (returns fig)
def plot_elevation_area_chart(elevation_data):
    elevations = [pt[2] for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    elevations_ft = [e * 3.28084 for e in elevations]

    segment_distances = [0]
    coords = [(pt[1], pt[0]) for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    for i in range(1, len(coords)):
        segment_distances.append(segment_distances[-1] + geodesic(coords[i - 1], coords[i]).miles)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(segment_distances, elevations_ft, color='lightblue', alpha=0.7)
    ax.plot(segment_distances, elevations_ft, color='blue', linewidth=2)
    ax.set_title("Elevation Profile of Route")
    ax.set_xlabel("Distance along route (miles)")
    ax.set_ylabel("Elevation (feet)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig

# 📈 Cumulative Elevation Gain Plot (returns fig)
def plot_cumulative_elevation_gain(elevation_data):
    elevations = [pt[2] * 3.28084 for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    cumulative_gain = [0]
    for i in range(1, len(elevations)):
        delta = elevations[i] - elevations[i - 1]
        cumulative_gain.append(cumulative_gain[-1] + max(0, delta))

    segment_distances = [0]
    coords = [(pt[1], pt[0]) for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    for i in range(1, len(coords)):
        segment_distances.append(segment_distances[-1] + geodesic(coords[i - 1], coords[i]).miles)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(segment_distances, cumulative_gain, color='green', linewidth=2)
    ax.set_title("Cumulative Elevation Gain (ft)")
    ax.set_xlabel("Distance along route (miles)")
    ax.set_ylabel("Cumulative Gain (feet)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig

# 📈 Moving Average Grade % Plot (returns fig)
def plot_moving_average_grade(elevation_data, window_size=5):
    elevations = [pt[2] for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    segment_distances = [0]
    coords = [(pt[1], pt[0]) for pt in elevation_data["geometry"]["coordinates"] if len(pt) > 2]
    for i in range(1, len(coords)):
        segment_distances.append(segment_distances[-1] + geodesic(coords[i - 1], coords[i]).miles)

    grade_percent = []
    for i in range(1, len(elevations)):
        delta_elev_ft = (elevations[i] - elevations[i - 1]) * 3.28084
        delta_dist_mi = segment_distances[i] - segment_distances[i - 1]
        grade = (delta_elev_ft / (delta_dist_mi * 5280)) * 100 if delta_dist_mi > 0 else 0
        grade_percent.append(grade)

    grade_percent_smoothed = pd.Series(grade_percent).rolling(window=window_size, min_periods=1, center=True).mean()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(segment_distances[1:], grade_percent_smoothed, color='purple', linewidth=2)
    ax.set_title(f"Moving Average Grade (window = {window_size})")
    ax.set_xlabel("Distance along route (miles)")
    ax.set_ylabel("Grade (%)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig

# 🏃‍♂️ Run Summary Printer (Streamlit safe)
def print_run_summary(route_coords, elevation_data, st):
    true_miles = calculate_route_distance(route_coords) / 1609.34
    ascent, descent = calculate_ascent_descent(elevation_data)
    net_change = ascent - descent
    net_change_abs = abs(net_change)

    summary = f"""
    ### 🏃‍♂️ Run Summary  
    **Distance:** {true_miles:.2f} mi  
    ⬆️ **Ascent:** {ascent:.0f} ft  
    ⬇️ **Descent:** {descent:.0f} ft  
    ↕️ **Net Elevation Change:** {net_change_abs:.0f} ft
    """
    st.markdown(summary)

# 📁 GPX Export
def save_route_as_gpx(coords, filename="running_route.gpx"):
    if not coords:
        print("❌ No route coordinates to save.")
        return

    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for lat, lon in coords:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

    with open(filename, "w") as f:
        f.write(gpx.to_xml())

    print(f"✅ GPX route saved as: {filename}")