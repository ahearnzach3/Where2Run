# app.py (UPDATED for route_environment selection)

import streamlit as st
import Where2Run_backend as wr
from streamlit.components.v1 import html
from streamlit_searchbox import st_searchbox

st.markdown("<h1 style='text-align: center;'>🏃‍♂️ Where2Run - Run Route Generator</h1>", unsafe_allow_html=True)
st.markdown("### 🚗 Powered by OpenRouteService + OpenStreetMap + Elevation Data")

with st.expander("ℹ️ About location geocoding (click to expand)"):
    st.write("Location lookup (geocoding) uses free OpenStreetMap Nominatim service. If it times out, just try again! It's a known limitation of free geocoding.")

# Tabs
route_tabs = st.tabs(["🔁 Loop", "↔️ Out-and-Back", "🏁 Destination"])

# --- LOOP TAB ---
with route_tabs[0]:
    st.markdown("## 🔁 Loop Route Generator")
    st.markdown("---")

    selected_place = st_searchbox(
        search_function=wr.search_places,
        placeholder="📍 Start typing your location (e.g., 400 E Morehead St, Charlotte, NC)",
        label="Starting Location",
        key="loop_start_search"
    )
    start_coords = selected_place if selected_place else None

    distance_miles = st.number_input("📏 Desired loop distance (miles)", min_value=1.0, value=6.0, step=0.5, key="loop_distance")
    use_preset = st.checkbox("🌉 Include Bridges preset?", key="loop_preset")
    include_destination = st.checkbox("📍 Include destination on loop?", key="loop_include_dest")
    destination_coords = None

    route_env = st.radio("🏙️ Route Type", ["Trail", "Suburban", "Urban"], key="loop_env")

    if include_destination:
        selected_dest = st_searchbox(
            search_function=wr.search_places,
            placeholder="🏁 Start typing your destination (e.g., Freedom Park, Charlotte NC)",
            label="Destination",
            key="loop_dest_search"
        )
        destination_coords = selected_dest if selected_dest else None
        st.caption("📍 Destination will be included as part of the loop — your route will pass through it before returning.")

    st.markdown("---")

    if st.button("Generate Loop Route 🚀", key="loop_button"):
        if start_coords:
            with st.spinner("Generating loop route..."):
                preset_coords = wr.bridges_route_coords if use_preset else None
                if include_destination and destination_coords:
                    route_coords, _ = wr.try_route_with_fallback(
                        wr.generate_loop_with_included_destination_v3,
                        start_coords=start_coords,
                        target_miles=distance_miles,
                        dest_coords=destination_coords,
                        bridges_coords=preset_coords,
                        route_environment=route_env
                    )
                else:
                    route_coords, _ = wr.try_route_with_fallback(
                        wr.generate_loop_route_with_preset_retry,
                        start_coords=start_coords,
                        distance_miles=distance_miles,
                        bridges_coords=preset_coords,
                        route_environment=route_env
                    )
                wr.display_route_results(route_coords, st)
        else:
            st.error("❌ Please enter a valid starting location.")

# --- OUT-AND-BACK TAB ---
with route_tabs[1]:
    st.markdown("## ↔️ Out-and-Back Route Generator")
    st.markdown("---")

    selected_place = st_searchbox(
        search_function=wr.search_places,
        placeholder="📍 Start typing your location (e.g., 400 E Morehead St, Charlotte, NC)",
        label="Starting Location",
        key="out_start_search"
    )
    start_coords = selected_place if selected_place else None


    distance_miles = st.number_input("📏 Total out-and-back distance (miles)", min_value=1.0, value=6.0, step=0.5, key="out_distance")
    direction_preference = st.selectbox("🎯 Bias route in direction?", ["None", "N", "S", "E", "W"], key="out_direction")
    route_env = st.radio("🏙️ Route Type", ["Trail", "Suburban", "Urban"], key="out_env")

    st.markdown("---")

    if st.button("Generate Out-and-Back Route 🚀", key="out_button"):
        if start_coords:
            with st.spinner("Generating out-and-back route..."):
                route_coords, _ = wr.try_route_with_fallback(
                    wr.generate_out_and_back_directional_route,
                    start_coords=start_coords,
                    distance_miles=distance_miles,
                    direction=direction_preference.lower() if direction_preference != "None" else "n",
                    route_environment=route_env
                )
                wr.display_route_results(route_coords, st)
        else:
            st.error("❌ Please enter a valid starting location.")

# --- DESTINATION TAB ---
with route_tabs[2]:
    st.markdown("## 🏁 Destination Route Generator")
    st.markdown("---")

    if "dest_flow_stage" not in st.session_state:
        st.session_state.dest_flow_stage = "initial"

    selected_place = st_searchbox(
        search_function=wr.search_places,
        placeholder="📍 Start typing your location (e.g., 400 E Morehead St, Charlotte, NC)",
        label="Starting Location",
        key="dest_start_search"
    )
    start_coords = selected_place if selected_place else None

    selected_dest = st_searchbox(
        search_function=wr.search_places,
        placeholder="🏁 Start typing your destination (e.g., Freedom Park, Charlotte NC)",
        label="Destination",
        key="dest_dest_search"
    )
    destination_coords = selected_dest if selected_dest else None

    st.markdown("---")

    if st.button("Generate Destination Route 🚀", key="dest_button"):
        if start_coords and destination_coords:
            with st.spinner("Generating destination route..."):
                route_coords, one_way_miles = wr.generate_destination_route(start_coords, destination_coords)
                if route_coords:
                    wr.display_route_results(route_coords, st)
                    st.session_state.dest_flow_stage = "post_initial"
                    st.session_state.dest_one_way_miles = one_way_miles
                    st.session_state.dest_start_coords = start_coords
                    st.session_state.dest_destination_coords = destination_coords
                else:
                    st.error("❌ Route could not be generated.")
        else:
            st.error("❌ Please enter both a valid starting location and destination.")

    if st.session_state.dest_flow_stage == "post_initial":
        st.write(f"❓ Distance to {st.session_state.dest_destination_coords} is {st.session_state.dest_one_way_miles:.2f} miles.")
        first_decision = st.radio("👉 Do you want to run this exact route?", ["Yes", "No"], key="dest_first_decision_radio")

        if first_decision == "No":
            second_decision = st.radio("👉 Do you want to 'extend' the route or make it a 'round trip'?", ["Extend", "Round Trip"], key="dest_second_decision_radio")

            if second_decision == "Round Trip":
                rt_coords = wr.generate_destination_round_trip(
                    st.session_state.dest_start_coords,
                    st.session_state.dest_destination_coords
                )
                wr.display_route_results(rt_coords, st)

            elif second_decision == "Extend":
                route_env = st.radio("🏙️ Route Type", ["Trail", "Suburban", "Urban"], key="dest_extend_env")

                target_miles = st.number_input(
                    f"🎯 Enter target total distance (must be >= {st.session_state.dest_one_way_miles:.2f} miles)",
                    min_value=st.session_state.dest_one_way_miles,
                    value=st.session_state.dest_one_way_miles + 2.0,
                    step=0.5,
                    key="dest_target_miles_input"
                )

                if st.button("Generate Extended Destination Route 🚀", key="dest_extend_button"):
                    extended_coords, _ = wr.try_route_with_fallback(
                        wr.generate_extended_destination_route,
                        start_coords=st.session_state.dest_start_coords,
                        dest_coords=st.session_state.dest_destination_coords,
                        target_miles=target_miles,
                        route_environment=route_env
                    )
                    wr.display_route_results(extended_coords, st)
