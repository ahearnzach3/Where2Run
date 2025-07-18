# app.py (FINAL Polished UI + Tabs + Large Map + Safe Download + Session State)

import streamlit as st
import Where2Run_backend as wr
from streamlit.components.v1 import html
from streamlit_searchbox import st_searchbox

# App title
st.markdown("<h1 style='text-align: center;'>🏃‍♂️ Where2Run - Run Route Generator</h1>", unsafe_allow_html=True)
st.markdown("### 🚗 Powered by OpenRouteService + OpenStreetMap + Elevation Data")

# Helpful note about geocoding timeouts
with st.expander("ℹ️ About location geocoding (click to expand)"):
    st.write("Location lookup (geocoding) uses free OpenStreetMap Nominatim service. If it times out, just try again! It's a known limitation of free geocoding.")

# Tabs for route types
tab_loop, tab_out_and_back, tab_destination = st.tabs(["🔁 Loop", "↔️ Out-and-Back", "🏁 Destination"])

# --- LOOP TAB ---
with tab_loop:
    st.markdown("## 🔁 Loop Route Generator")
    st.markdown("---")

    with st.container():
        # 📍 Searchbox Input (Mapbox UI — returns lat/lon and stores label)
        st_searchbox(
            search_function=wr.search_places,
            placeholder="Start typing your starting address (e.g., 400 E Morehead St, Charlotte, NC)",
            label="📍 Enter your starting location",
            key="loop_start_search"
        )

        # ✅ Extract label (place_name) from session state and convert via Nominatim
        start_label = st.session_state.get("loop_start_search", {}).get("result")
        # start_coords = wr.get_coordinates(start_label) if start_label else None
        start_coords = wr.get_coordinates(start_label, st) if start_label else None # Temp


        # 📏 Distance Input
        distance_miles = st.number_input(
            "📏 Desired loop distance (miles)",
            min_value=1.0, value=6.0, step=0.5,
            key="loop_distance"
        )

        # 🌉 Bridges preset
        use_preset = st.checkbox("🌉 Include Bridges preset?", key="loop_preset")

        # 🧭 Route Environment Preference (Expanded Options)
        route_env = st.selectbox(
            "🌿 Route Environment Preference (Optional)", 
            ["None", "Prefer Trails", "Scenic", "Shaded", "Suburban", "Urban"], 
            key="loop_env_select"
        )
        route_env = None if route_env == "None" else route_env.lower()

        # 🏁 Optional Destination Location
        include_destination = st.checkbox("📍 Include destination on loop?", key="loop_include_dest")
        destination_coords = None

        if include_destination:
            st_searchbox(
                search_function=wr.search_places,
                placeholder="Enter destination location (e.g., Freedom Park, Charlotte, NC)",
                label="🏁 Destination address",
                key="loop_dest_search"
            )

            dest_label = st.session_state.get("loop_dest_search", {}).get("result")
            destination_coords = wr.get_coordinates(dest_label) if dest_label else None

            st.caption("📍 Destination will be included as part of the loop — your route will pass through it before returning.")

    st.markdown("---")

    if st.button("Generate Loop Route 🚀", key="loop_button"):
        if start_coords:
            with st.spinner("Generating loop route..."):
                preset_coords = wr.bridges_route_coords if use_preset else None

                if include_destination and destination_coords:
                    route_coords = wr.generate_loop_with_included_destination_v3(
                        start_coords=start_coords,
                        target_miles=distance_miles,
                        dest_coords=destination_coords,
                        bridges_coords=preset_coords,
                        route_environment=route_env 
                    )
                else:
                    route_coords = wr.generate_loop_route_with_preset_retry(
                        start_coords=start_coords,
                        distance_miles=distance_miles,
                        bridges_coords=preset_coords,
                        route_environment=route_env
                    )

                if route_coords:
                    elevation_data = wr.get_elevation_for_coords(route_coords)
                    m = wr.plot_route_with_elevation(route_coords, elevation_data)

                    route_length_miles = wr.calculate_route_distance(route_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))

                    html(m.get_root().render(), height=map_height, scrolling=True)

                    wr.print_run_summary(route_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        st.pyplot(wr.plot_elevation_area_chart(elevation_data))
                        st.pyplot(wr.plot_cumulative_elevation_gain(elevation_data))
                        st.pyplot(wr.plot_moving_average_grade(elevation_data))

                    wr.save_route_as_gpx(route_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="loop_gpx_download")
                else:
                    st.error("❌ Route could not be generated.")
        else:
            st.error("❌ Please enter a valid starting location.")



with tab_out_and_back:
    st.markdown("## ↔️ Out-and-Back Route Generator")
    st.markdown("---")

    with st.container():
        # 📍 Start Location with Mapbox Searchbox
        st_searchbox(
            search_function=wr.search_places,
            placeholder="📍 Start typing your location (e.g., 400 E Morehead St, Charlotte, NC)",
            label="Starting Location",
            key="out_start_search"
        )

        # ✅ Convert label to (lat, lon) using same method as Loop tab
        start_label = st.session_state.get("out_start_search", {}).get("result")
        start_coords = wr.get_coordinates(start_label) if start_label else None
        # st.write("📍 Debug - Start Coords:", start_coords)

        distance_miles = st.number_input(
            "📏 Total out-and-back distance (miles)", 
            min_value=1.0, value=6.0, step=0.5, 
            key="out_distance"
        )

        direction_preference = st.selectbox(
            "🎯 Bias route in direction (Optional)", 
            ["None", "N", "S", "E", "W"], 
            key="out_direction"
        )

        # 🧭 Route Environment Preference (Expanded Options)
        route_env = st.selectbox(
            "🌿 Route Environment Preference (Optional)", 
            ["None", "Prefer Trails", "Scenic", "Shaded", "Suburban", "Urban"], 
            key="out_env_select"
        )
        route_env = None if route_env == "None" else route_env.lower()

    st.markdown("---")

    if st.button("Generate Out-and-Back Route 🚀", key="out_button"):
        if start_coords:
            with st.spinner("Generating out-and-back route..."):
                try:
                    route_coords = wr.generate_out_and_back_directional_route(
                        start_coords=start_coords,
                        distance_miles=distance_miles,
                        direction=direction_preference.lower() if direction_preference != "None" else "n",
                        route_environment=route_env
                    )
                    if route_coords:
                        elevation_data = wr.get_elevation_for_coords(route_coords)
                        m = wr.plot_route_with_elevation(route_coords, elevation_data)

                        route_length_miles = wr.calculate_route_distance(route_coords) / 1609.34
                        map_height = min(800, 400 + int(route_length_miles * 20))

                        map_html = m.get_root().render()
                        html(map_html, height=map_height, scrolling=True)

                        wr.print_run_summary(route_coords, elevation_data, st)

                        with st.expander("📈 Elevation Charts (click to expand)"):
                            st.pyplot(wr.plot_elevation_area_chart(elevation_data))
                            st.pyplot(wr.plot_cumulative_elevation_gain(elevation_data))
                            st.pyplot(wr.plot_moving_average_grade(elevation_data))

                        wr.save_route_as_gpx(route_coords, filename="Where2Run_route.gpx")
                        with open("Where2Run_route.gpx", "rb") as file:
                            st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="out_gpx_download")
                    else:
                        st.error("❌ Route could not be generated.")
                        st.info("Try changing direction, distance, or environment preference.")

                        # 🔍 Developer debug info (optional, remove for production)
                        st.code(f"Debug — Start Coords: {start_coords}")
                except ValueError as ve:
                    st.error(f"❌ Input error: {ve}")
                    st.code(f"Start Coords: {start_coords}")
                except Exception as e:
                    st.error("❌ Unexpected error occurred during routing.")
                    st.code(str(e))
        else:
            st.error("❌ Please enter a valid starting location.")


# --- DESTINATION TAB ---
with tab_destination:
    st.markdown("## 🏁 Destination Route Generator")
    st.markdown("---")

    if "dest_flow_stage" not in st.session_state:
        st.session_state.dest_flow_stage = "initial"

    with st.container():
        # 📍 Searchbox Inputs (Mapbox UI — returns lat/lon and stores label)
        st_searchbox(
            search_function=wr.search_places,
            placeholder="Start typing your starting address (e.g., 400 E Morehead St, Charlotte, NC)",
            label="📍 Enter your starting location",
            key="dest_start_search"
        )
        st_searchbox(
            search_function=wr.search_places,
            placeholder="Enter destination location (e.g., Freedom Park, Charlotte, NC)",
            label="🏁 Destination address",
            key="dest_dest_search"
        )

        # ✅ Extract the selected place_name (label) for each
        start_label = st.session_state.get("dest_start_search", {}).get("result")
        dest_label = st.session_state.get("dest_dest_search", {}).get("result")

        # 🌍 Use Nominatim to geocode to coordinates
        start_coords = wr.get_coordinates(start_label) if start_label else None
        destination_coords = wr.get_coordinates(dest_label) if dest_label else None

    st.markdown("---")

    if st.button("Generate Destination Route 🚀", key="dest_button"):
        if start_coords and destination_coords:
            with st.spinner("Generating destination route..."):
                route_coords, one_way_miles = wr.generate_destination_route(
                    start_coords=start_coords,
                    dest_coords=destination_coords,
                    elevation_preference="Normal",
                )

                if route_coords:
                    elevation_data = wr.get_elevation_for_coords(route_coords)
                    m = wr.plot_route_with_elevation(route_coords, elevation_data)

                    route_length_miles = wr.calculate_route_distance(route_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))

                    html(m.get_root().render(), height=map_height, scrolling=True)

                    wr.print_run_summary(route_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        st.pyplot(wr.plot_elevation_area_chart(elevation_data))
                        st.pyplot(wr.plot_cumulative_elevation_gain(elevation_data))
                        st.pyplot(wr.plot_moving_average_grade(elevation_data))

                    wr.save_route_as_gpx(route_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button("Download GPX", data=file, file_name="Where2Run_route.gpx", key="dest_gpx_download_initial")

                    st.session_state.dest_flow_stage = "post_initial"
                    st.session_state.dest_one_way_miles = one_way_miles
                    st.session_state.dest_start_coords = start_coords
                    st.session_state.dest_destination_coords = destination_coords
                else:
                    st.error("❌ Route could not be generated.")
        else:
            st.error("❌ Please enter both a valid starting location and destination.")

    # Post-initial logic
    if st.session_state.dest_flow_stage == "post_initial":
        st.write(f"❓ Distance to destination is {st.session_state.dest_one_way_miles:.2f} miles.")
        first_decision = st.radio("🔀 Do you want to run this exact route?", ["Yes", "No"], key="dest_first_decision_radio")

        if first_decision == "Yes":
            pass

        elif first_decision == "No":
            second_decision = st.radio("🔀 Do you want to 'extend' the route or make it a 'round trip'?", ["Extend", "Round Trip"], key="dest_second_decision_radio")

            if second_decision == "Round Trip":
                rt_coords = wr.generate_destination_round_trip(
                    st.session_state.dest_start_coords,
                    st.session_state.dest_destination_coords
                )
                if rt_coords:
                    elevation_data = wr.get_elevation_for_coords(rt_coords)
                    m = wr.plot_route_with_elevation(rt_coords, elevation_data)

                    route_length_miles = wr.calculate_route_distance(rt_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))

                    html(m.get_root().render(), height=map_height, scrolling=True)

                    wr.print_run_summary(rt_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        st.pyplot(wr.plot_elevation_area_chart(elevation_data))
                        st.pyplot(wr.plot_cumulative_elevation_gain(elevation_data))
                        st.pyplot(wr.plot_moving_average_grade(elevation_data))

                    wr.save_route_as_gpx(rt_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button("Download GPX", data=file, file_name="Where2Run_route.gpx", key="dest_gpx_download_roundtrip")

            elif second_decision == "Extend":
                target_miles = st.number_input(
                    f"🌟 Enter target total distance (must be ≥ {st.session_state.dest_one_way_miles:.2f} miles)",
                    min_value=st.session_state.dest_one_way_miles,
                    value=st.session_state.dest_one_way_miles + 2.0,
                    step=0.5,
                    key="dest_target_miles_input"
                )

                if st.button("Generate Extended Destination Route 🚀", key="dest_extend_button"):
                    extended_coords = wr.generate_extended_destination_route(
                        st.session_state.dest_start_coords,
                        st.session_state.dest_destination_coords,
                        target_miles
                    )
                    if extended_coords:
                        elevation_data = wr.get_elevation_for_coords(extended_coords)
                        m = wr.plot_route_with_elevation(extended_coords, elevation_data)

                        route_length_miles = wr.calculate_route_distance(extended_coords) / 1609.34
                        map_height = min(800, 400 + int(route_length_miles * 20))

                        html(m.get_root().render(), height=map_height, scrolling=True)

                        wr.print_run_summary(extended_coords, elevation_data, st)

                        with st.expander("📈 Elevation Charts (click to expand)"):
                            st.pyplot(wr.plot_elevation_area_chart(elevation_data))
                            st.pyplot(wr.plot_cumulative_elevation_gain(elevation_data))
                            st.pyplot(wr.plot_moving_average_grade(elevation_data))

                        wr.save_route_as_gpx(extended_coords, filename="Where2Run_route.gpx")
                        with open("Where2Run_route.gpx", "rb") as file:
                            st.download_button("Download GPX", data=file, file_name="Where2Run_route.gpx", key="dest_gpx_download_extended")
                            