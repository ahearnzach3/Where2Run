
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
  - Scenic and shaded route logic powered by Overpass API and real-time fallback logic
- Interactive route map with elevation heatmap overlay
- Downloadable GPX files for watch or app syncing

---

## 🧠 Smart Features

- 🧭 **Environment-aware routing**: Avoids busy roads, favors trails or shaded streets
- 🏁 **Destination-based runs**: Run *to* a location, extend the distance, or generate round trips
- 🧱 **Modular architecture**: All route types handled by clean backend logic
- 🧠 **Session-aware UI**: Caches user state, locations, and preferences
- 📥 **One-click GPX export** for Garmin, Strava, etc.

---

## Features in Development

- **Integrated Training Plans**  
  Supports structured race prep (Marathon, Half) with visual progress tracking and countdown to race day  
  Future integration with real-world race GPX files and calendar syncing

- **Personalized Route Logic**  
  Automatically suggest routes based on user behavior and training plan history

- **Elevation-based filtering**
  Prefer hills or flat routes based on training goals 

---

## 🛠 Tech Stack

- **Frontend**: Streamlit, Folium, HTML Embeds  
- **Backend**: Python, OpenRouteService API, Overpass API  
- **Geocoding**: LocationIQ  
- **Data Handling**: Pandas, NumPy  
- **DevOps**: Streamlit Cloud, GitHub Actions (future)  
- **Database (In Development)**: Supabase (user auth, caching)

---

## 🎯 Why I Built This

I’m currently training for another marathon, and I wanted a tool that not only supports my daily runs but aligns with my broader fitness goals. Most running apps felt either too rigid or locked behind paywalls.

Where2Run was born from my desire to merge two of my biggest passions — data and health. As a lifelong athlete and a dedicated data engineer, I wanted to build something that could evolve with my training while giving me the freedom to experiment, learn, and grow. This project isn’t just a tool for runners — it’s a reflection of my belief that data can empower better habits, smarter planning, and healthier lives.

Where2Run is the perfect intersection of my interests and a hands-on way for me to become a stronger, more well-rounded data engineer.

---

## Notes

- Start locations work best with full addresses  
- Some business names may not resolve due to OSM search limitations

---

## License

This project is licensed for personal, non-commercial use only.  
All rights reserved © 2025 Zachary Ahearn.  
For licensing inquiries, contact the author directly.

---

## Acknowledgements

- [OpenRouteService](https://openrouteservice.org)  
- [OpenStreetMap](https://www.openstreetmap.org)  
- [Streamlit](https://streamlit.io)
