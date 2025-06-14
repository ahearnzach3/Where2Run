# app.py (FINAL Polished UI + Tabs + Large Map + Safe Download + Session State)

import streamlit as st
import Where2Run_backend as wr
from streamlit.components.v1 import html
from Where2Run_backend import mapbox_autocomplete  # Used for Address Autocompletion
from Where2Run_backend import get_coords_from_place_name # Used for Address Autocompletion

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
        # 📍 Start Location with Autocomplete + Placeholder
        typed_start = st.text_input(
            "📍 Start typing your location",
            placeholder="e.g., 400 E Morehead St, Charlotte, NC → (Dowd YMCA)",
            key="loop_start_typed"
        )
        start_suggestions = wr.mapbox_autocomplete(typed_start) if typed_start else []
        start_options = ["🔍 Choose from suggestions..."] + start_suggestions if start_suggestions else []
        start_location = st.selectbox("Choose your starting location", start_options, key="loop_start_select") if start_options else None
        start_coords = wr.get_coords_from_place_name(start_location) if start_location and start_location != "🔍 Choose from suggestions..." else None

        # 📏 Distance Input
        distance_miles = st.number_input("📏 Desired loop distance (miles)", min_value=1.0, value=6.0, step=0.5, key="loop_distance")

        # 🌉 Bridges preset
        use_preset = st.checkbox("🌉 Include Bridges preset?", key="loop_preset")

        # 📍 Destination Location with Autocomplete + Placeholder
        include_destination = st.checkbox("📍 Include destination on loop?", key="loop_include_dest")
        destination_coords = None

        if include_destination:
            typed_dest = st.text_input(
                "🏁 Start typing your destination",
                placeholder="e.g., Freedom Park, Charlotte NC",
                key="loop_dest_typed"
            )
            dest_suggestions = wr.mapbox_autocomplete(typed_dest) if typed_dest else []
            dest_options = ["🔍 Choose from suggestions..."] + dest_suggestions if dest_suggestions else []
            selected_dest = st.selectbox("Choose your destination", dest_options, key="loop_dest_select") if dest_options else None
            destination_coords = wr.get_coords_from_place_name(selected_dest) if selected_dest and selected_dest != "🔍 Choose from suggestions..." else None

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
                        bridges_coords=preset_coords
                    )
                else:
                    route_coords = wr.generate_loop_route_with_preset_retry(
                        start_coords=start_coords,
                        distance_miles=distance_miles,
                        bridges_coords=preset_coords
                    )

                if route_coords:
                    elevation_data = wr.get_elevation_for_coords(route_coords)
                    m = wr.plot_route_with_elevation(route_coords, elevation_data)

                    # Dynamic map height based on route length
                    route_length_miles = wr.calculate_route_distance(route_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))
                    
                    map_html = m.get_root().render()
                    html(map_html, height=map_height, scrolling=True)
 

                    wr.print_run_summary(route_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        fig1 = wr.plot_elevation_area_chart(elevation_data)
                        st.pyplot(fig1)

                        fig2 = wr.plot_cumulative_elevation_gain(elevation_data)
                        st.pyplot(fig2)

                        fig3 = wr.plot_moving_average_grade(elevation_data)
                        st.pyplot(fig3)

                    wr.save_route_as_gpx(route_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="loop_gpx_download")
                else:
                    st.error("❌ Route could not be generated.")
        else:
            st.error("❌ Please enter a valid starting location.")

# --- OUT-AND-BACK TAB ---
with tab_out_and_back:
    st.markdown("## ↔️ Out-and-Back Route Generator")
    st.markdown("---")

    with st.container():
        start_location = st.text_input(
    "📍 Enter your starting location", placeholder="e.g., 400 E Morehead St, Charlotte, NC --> (Dowd YMCA)", key="out_start")
        start_coords = wr.get_coordinates(start_location) if start_location else None

        distance_miles = st.number_input("📏 Total out-and-back distance (miles)", min_value=1.0, value=6.0, step=0.5, key="out_distance")
        direction_preference = st.selectbox("🎯 Bias route in direction?", ["None", "N", "S", "E", "W"], key="out_direction")

    st.markdown("---")

    if st.button("Generate Out-and-Back Route 🚀", key="out_button"):
        if start_coords:
            with st.spinner("Generating out-and-back route..."):
                route_coords = wr.generate_out_and_back_directional_route(
                    start_coords=start_coords,
                    distance_miles=distance_miles,
                    direction=direction_preference.lower() if direction_preference != "None" else "n"
                )
                if route_coords:
                    elevation_data = wr.get_elevation_for_coords(route_coords)
                    m = wr.plot_route_with_elevation(route_coords, elevation_data)

                    # Dynamic map height based on route length
                    route_length_miles = wr.calculate_route_distance(route_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))
                    
                    map_html = m.get_root().render()
                    html(map_html, height=map_height, scrolling=True)

                    wr.print_run_summary(route_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        fig1 = wr.plot_elevation_area_chart(elevation_data)
                        st.pyplot(fig1)

                        fig2 = wr.plot_cumulative_elevation_gain(elevation_data)
                        st.pyplot(fig2)

                        fig3 = wr.plot_moving_average_grade(elevation_data)
                        st.pyplot(fig3)

                    wr.save_route_as_gpx(route_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="out_gpx_download")
                else:
                    st.error("❌ Route could not be generated.")
        else:
            st.error("❌ Please enter a valid starting location.")

# --- DESTINATION TAB ---
with tab_destination:
    st.markdown("## 🏁 Destination Route Generator")
    st.markdown("---")

    # Init session state for destination flow
    if "dest_flow_stage" not in st.session_state:
        st.session_state.dest_flow_stage = "initial"

    with st.container():
        start_location = st.text_input(
    "📍 Enter your starting location", placeholder="e.g., 400 E Morehead St, Charlotte, NC --> (Dowd YMCA)", key="dest_start")
        start_coords = wr.get_coordinates(start_location) if start_location else None

        destination_address = st.text_input("🏁 Enter destination location", key="dest_dest_addr")
        destination_coords = wr.get_coordinates(destination_address) if destination_address else None

    st.markdown("---")

    if st.button("Generate Destination Route 🚀", key="dest_button"):
        if start_coords and destination_coords:
            with st.spinner("Generating destination route..."):
                route_coords, one_way_miles = wr.generate_destination_route(start_coords, destination_coords)
                if route_coords:
                    elevation_data = wr.get_elevation_for_coords(route_coords)
                    m = wr.plot_route_with_elevation(route_coords, elevation_data)

                    # Dynamic map height based on route length
                    route_length_miles = wr.calculate_route_distance(route_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))
                    
                    map_html = m.get_root().render()
                    html(map_html, height=map_height, scrolling=True)

                    wr.print_run_summary(route_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        fig1 = wr.plot_elevation_area_chart(elevation_data)
                        st.pyplot(fig1)

                        fig2 = wr.plot_cumulative_elevation_gain(elevation_data)
                        st.pyplot(fig2)

                        fig3 = wr.plot_moving_average_grade(elevation_data)
                        st.pyplot(fig3)

                    wr.save_route_as_gpx(route_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="dest_gpx_download_initial")

                    # Update session state
                    st.session_state.dest_flow_stage = "post_initial"
                    st.session_state.dest_one_way_miles = one_way_miles
                    st.session_state.dest_start_coords = start_coords
                    st.session_state.dest_destination_coords = destination_coords
                else:
                    st.error("❌ Route could not be generated.")
        else:
            st.error("❌ Please enter both a valid starting location and destination.")

    # Post initial flow (Extend / Round Trip)
    if st.session_state.dest_flow_stage == "post_initial":
        st.write(f"❓ Distance to {destination_address} is {st.session_state.dest_one_way_miles:.2f} miles.")
        first_decision = st.radio("👉 Do you want to run this exact route?", ["Yes", "No"], key="dest_first_decision_radio")

        if first_decision == "Yes":
            pass  # Done

        elif first_decision == "No":
            second_decision = st.radio("👉 Do you want to 'extend' the route or make it a 'round trip'?", ["Extend", "Round Trip"], key="dest_second_decision_radio")

            if second_decision == "Round Trip":
                rt_coords = wr.generate_destination_round_trip(
                    st.session_state.dest_start_coords,
                    st.session_state.dest_destination_coords
                )
                if rt_coords:
                    elevation_data = wr.get_elevation_for_coords(rt_coords)
                    m = wr.plot_route_with_elevation(rt_coords, elevation_data)

                    # Dynamic map height based on route length
                    route_length_miles = wr.calculate_route_distance(rt_coords) / 1609.34
                    map_height = min(800, 400 + int(route_length_miles * 20))
                    
                    map_html = m.get_root().render()
                    html(map_html, height=map_height, scrolling=True)

                    wr.print_run_summary(rt_coords, elevation_data, st)

                    with st.expander("📈 Elevation Charts (click to expand)"):
                        fig1 = wr.plot_elevation_area_chart(elevation_data)
                        st.pyplot(fig1)

                        fig2 = wr.plot_cumulative_elevation_gain(elevation_data)
                        st.pyplot(fig2)

                        fig3 = wr.plot_moving_average_grade(elevation_data)
                        st.pyplot(fig3)

                    wr.save_route_as_gpx(rt_coords, filename="Where2Run_route.gpx")
                    with open("Where2Run_route.gpx", "rb") as file:
                        st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="dest_gpx_download_roundtrip")

            elif second_decision == "Extend":
                target_miles = st.number_input(f"🎯 Enter target total distance (must be >= {st.session_state.dest_one_way_miles:.2f} miles)", min_value=st.session_state.dest_one_way_miles, value=st.session_state.dest_one_way_miles + 2.0, step=0.5, key="dest_target_miles_input")
                if st.button("Generate Extended Destination Route 🚀", key="dest_extend_button"):
                    extended_coords = wr.generate_extended_destination_route(
                        st.session_state.dest_start_coords,
                        st.session_state.dest_destination_coords,
                        target_miles
                    )
                    if extended_coords:
                        elevation_data = wr.get_elevation_for_coords(extended_coords)
                        m = wr.plot_route_with_elevation(extended_coords, elevation_data)
                        
                        # Dynamic map height based on route length
                        route_length_miles = wr.calculate_route_distance(extended_coords) / 1609.34
                        map_height = min(800, 400 + int(route_length_miles * 20))
                        
                        map_html = m.get_root().render()
                        html(map_html, height=map_height, scrolling=True)

                        wr.print_run_summary(extended_coords, elevation_data, st)

                        with st.expander("📈 Elevation Charts (click to expand)"):
                            fig1 = wr.plot_elevation_area_chart(elevation_data)
                            st.pyplot(fig1)

                            fig2 = wr.plot_cumulative_elevation_gain(elevation_data)
                            st.pyplot(fig2)

                            fig3 = wr.plot_moving_average_grade(elevation_data)
                            st.pyplot(fig3)

                        wr.save_route_as_gpx(extended_coords, filename="Where2Run_route.gpx")
                        with open("Where2Run_route.gpx", "rb") as file:
                            st.download_button(label="Download GPX", data=file, file_name="Where2Run_route.gpx", key="dest_gpx_download_extended")
