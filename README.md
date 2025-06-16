# Where2Run - Intelligent Route Planning for Runners

**Where2Run** is a purpose-built running platform that helps athletes plan smarter, more personalized routes based on location, terrain, and training needs.

It combines high-quality open-source routing data with real-time logic to generate diverse, environment-aware routes that can be customized by distance, direction, or destination.

Core functionality includes:

- Routing powered by OpenRouteService and OpenStreetMap
- Elevation-aware mapping and distance calibration
- Multiple route modes:
  - Loop
  - Out-and-Back (with directional bias)
  - Destination-based runs
  - Extended or round-trip options

---

## Live App

https://where2run-beta.streamlit.app

---

## Key Features

- Input your starting location (address or coordinates)
- Select route type and target mileage
- Optional features:
  - Add scenic waypoints or destinations
  - Include preset route segments (e.g., bridge routes)
  - Filter by route environment (trails, shaded, urban, etc.)
- Interactive route map with elevation heatmap overlay
- Downloadable GPX files for watch or app syncing

---

## Features in Development

- **Integrated Training Plans**  
  Supports structured race prep (Marathon, Half) with visual progress tracking and countdown to race day  
  Future integration with real-world race GPX files and calendar syncing

- **Environment-Based Routing Filters**  
  Scenic and shaded route logic powered by Overpass API and real-time fallback logic

- **Personalized Route Logic**  
  Automatically suggest routes based on user behavior and training plan history

---

## Notes

- Start locations work best with full addresses  
- Some business names may not resolve due to OSM search limitations

---

## License

MIT License

---

## Acknowledgements

- [OpenRouteService](https://openrouteservice.org)  
- [OpenStreetMap](https://www.openstreetmap.org)  
- [Streamlit](https://streamlit.io)
