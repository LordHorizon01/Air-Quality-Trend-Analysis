import streamlit as st
import requests
import os
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium

# Loaded API key
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

st.set_page_config(page_title="Real-Time AQI", layout="wide")

st.title("🌍 Real-Time Air Quality Index")
st.markdown("Check real-time AQI and pollutant levels for any city or click on map")

# SESSION STATE
if "city_input" not in st.session_state:
    st.session_state.city_input = "Delhi"

if "lat" not in st.session_state:
    st.session_state.lat = None

if "lon" not in st.session_state:
    st.session_state.lon = None

if "aqi_data" not in st.session_state:
    st.session_state.aqi_data = None

#  AQI CATEGORY 
def get_aqi_info(aqi):
    return {
        1: ("Good", "green"),
        2: ("Fair", "lightgreen"),
        3: ("Moderate", "yellow"),
        4: ("Poor", "orange"),
        5: ("Very Poor", "red")
    }.get(aqi, ("Unknown", "gray"))

def get_aqi_range(aqi):
    return{
        1:"0-50",
        2:"51-100",
        3:"101-200",
        4:"201-300",
        5:"301-500"
    }.get(aqi, "Unknown")
# INPUT 
city_input = st.text_input("🏙️ Enter City Name", value=st.session_state.city_input)

selected_location = None

# CITY SEARCH 
if city_input and API_KEY:
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_input}&limit=5&appid={API_KEY}"
    geo_response = requests.get(geo_url).json()

    if isinstance(geo_response, list) and len(geo_response) > 0:
        options = []
        for loc in geo_response:
            label = f"{loc.get('name','')}, {loc.get('state','')}, {loc.get('country','')}"
            options.append((label, loc))

        selected_label = st.selectbox("📍 Select Location", [o[0] for o in options])

        for label, loc in options:
            if label == selected_label:
                selected_location = loc

#  BUTTONS 
col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Get AQI"):
        if selected_location:
            st.session_state.lat = selected_location["lat"]
            st.session_state.lon = selected_location["lon"]
            st.session_state.city_input = selected_label

        if not st.session_state.lat:
            st.error("Select location or click on map ❌")
        else:
            aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={st.session_state.lat}&lon={st.session_state.lon}&appid={API_KEY}"
            data = requests.get(aqi_url).json()

            if "list" in data:
                st.session_state.aqi_data = data
            else:
                st.error("Failed to fetch AQI ❌")

with col2:
    if st.button("🔄 Refresh"):
        st.session_state.aqi_data = None
        st.session_state.lat = None
        st.session_state.lon = None
        st.rerun()

# AQI DISPLAY 
if st.session_state.aqi_data:
    data = st.session_state.aqi_data
    aqi = data["list"][0]["main"]["aqi"]
    components = data["list"][0]["components"]

    category, color = get_aqi_info(aqi)

    st.markdown(f"""
    <div style="
        background:{color};
        padding:20px;
        border-radius:12px;
        text-align:center;
        color:black;
    ">
        
    <div style="
        top:10px;
        left:15px;
        background:white;
        padding:6px 12px;
        border-radius:12px;
        font-weight:bold;
        font-size:30px;
    ">
        AQI value lies between: {get_aqi_range(aqi)}
    </div>
        <h2>{st.session_state.city_input.upper()}</h2>
        <h1>AQI Category: {aqi}</h1>
        <h3>{category}</h3>
    </div>
    """, unsafe_allow_html=True)

    st.progress(aqi / 5)

    c1, c2 = st.columns(2)

    with c1:
        st.metric("PM2.5", components["pm2_5"])
        st.metric("PM10", components["pm10"])
        st.metric("CO", components["co"])
        st.metric("NO2", components["no2"])

    with c2:
        st.metric("O3", components["o3"])
        st.metric("SO2", components["so2"])
        st.metric("NH3", components["nh3"])

#  MAP
st.markdown("### 🗺️ Click Anywhere on Map")

# Decided center
if st.session_state.lat:
    center = [st.session_state.lat, st.session_state.lon]
    zoom = 5
else:
    center = [20, 0]
    zoom = 2   #  FULL WORLD MAP VIEW 

# Created map
m = folium.Map(
    location=center,
    zoom_start=zoom,
    tiles="CartoDB positron",
    max_bounds=True
)

# Added marker
if st.session_state.lat:
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Selected Location",
        icon=folium.Icon(color="red")
    ).add_to(m)

# Rendering map
map_data = st_folium(
    m,
    height=550,
    use_container_width=True,
    returned_objects=["last_clicked"]
)

# HANDLING CLICK 
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    # Preventing unnecessary rerender loop
    if st.session_state.lat != lat or st.session_state.lon != lon:

        st.session_state.lat = lat
        st.session_state.lon = lon

        # Reverse geocoding 
        try:
            reverse_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
            res = requests.get(reverse_url).json()

            if isinstance(res, list) and len(res) > 0:
                place = res[0]
                name = place.get("name", "")
                country = place.get("country", "")
                st.session_state.city_input = f"{name}, {country}"
            else:
                st.session_state.city_input = f"{lat:.4f}, {lon:.4f}"
        except:
            st.session_state.city_input = f"{lat:.4f}, {lon:.4f}"

        st.rerun()   #  controlled rerun only when needed