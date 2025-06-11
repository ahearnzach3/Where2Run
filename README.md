# 🏃‍♂️ Where2Run - Run Route Generator

**Where2Run** is a simple web app that generates running routes based on your input preferences, using:

- 🗺️ **OpenRouteService API** (for routing)
- 🌍 **OpenStreetMap** (underlying map data)
- 📈 Elevation charts (from elevation data)
- 🏃‍♂️ Multiple route types:
  - 🔁 Loop
  - ↔️ Out-and-Back
  - 🏁 Destination-based run
  - 🎯 Option to extend or round-trip destination runs

---

## 🚀 Live App

👉 [https://where2run-beta.streamlit.app](https://where2run-beta.streamlit.app)

---

## 🛠️ How It Works

### Features:

✅ Enter a starting location (address format recommended)  
✅ Choose your route type & distance  
✅ Optional: include a destination or preset route  
✅ See elevation-colored map and elevation charts  
✅ Download the route as GPX for your watch or app

---

## 💻 Running Locally

### Requirements:

- Python 3.8+
- Packages in `requirements.txt`:
  - streamlit
  - openrouteservice
  - folium
  - gpxpy
  - matplotlib
  - geopy
  - numpy
  - pandas

### Setup:

```bash
git clone https://github.com/ahearnzach3/Where2Run.git
cd Where2Run
pip install -r requirements.txt
streamlit run app.py

## 📌 Notes

Starting location works best with **full street address** (e.g., `400 E Morehead St, Charlotte, NC (Dowd YMCA)`).

Some business names may not resolve due to limitations of the free OpenStreetMap geocoder.

---

## ✨ Future Ideas

- Safety-focused routing
- Traffic & obstacle avoidance
- Shaded & scenic route filters
- Personalized routes based on user preferences
- Live re-routing during run
- Social & community features

---

## 📜 License

MIT License

---

## 🤝 Acknowledgements

- [OpenRouteService](https://openrouteservice.org)
- [OpenStreetMap](https://www.openstreetmap.org)
- Streamlit Cloud for deployment
