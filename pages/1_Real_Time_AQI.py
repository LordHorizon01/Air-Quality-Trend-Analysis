import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Real-Time AQI", layout="wide")

# ---------------- API KEY ----------------
API_KEY = st.secrets["OPENWEATHER_API_KEY"]

# ---------------- TITLE ----------------
st.title("🌍 Real-Time Air Quality Index")
st.markdown("Check real-time AQI and pollutant levels for any city or click on map")

# ---------------- SESSION STATE ----------------
if "city_input" not in st.session_state:
    st.session_state.city_input = "Delhi"

if "lat" not in st.session_state:
    st.session_state.lat = None

if "lon" not in st.session_state:
    st.session_state.lon = None

if "aqi_data" not in st.session_state:
    st.session_state.aqi_data = None

# ---------------- FUNCTIONS ----------------
def get_aqi_info(aqi):
    return {
        1: ("Good", "#00e400"),
        2: ("Fair", "#9cff9c"),
        3: ("Moderate", "#ffff00"),
        4: ("Poor", "#ff7e00"),
        5: ("Very Poor", "#ff0000")
    }.get(aqi, ("Unknown", "#cccccc"))


def get_aqi_range(aqi):
    return {
        1: "0 - 50",
        2: "51 - 100",
        3: "101 - 200",
        4: "201 - 300",
        5: "301 - 500"
    }.get(aqi, "Unknown")


# ---------------- INPUT ----------------
city_input = st.text_input(
    "🏙️ Enter City Name",
    value=st.session_state.city_input,
    key="city_box"
)

st.session_state.city_input = city_input

selected_location = None

# ---------------- CITY SEARCH ----------------
if city_input.strip():

    try:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_input}&limit=5&appid={API_KEY}"
        geo_response = requests.get(geo_url).json()

        if isinstance(geo_response, list) and len(geo_response) > 0:

            options = []
            for loc in geo_response:
                label = f"{loc.get('name','')}, {loc.get('state','')}, {loc.get('country','')}"
                options.append((label, loc))

            selected_label = st.selectbox(
                "📍 Select Location",
                [x[0] for x in options],
                key="location_select"
            )

            for label, loc in options:
                if label == selected_label:
                    selected_location = loc
                    break

    except:
        pass

# ---------------- BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Get AQI"):

        if selected_location:
            st.session_state.lat = selected_location["lat"]
            st.session_state.lon = selected_location["lon"]
            st.session_state.city_input = selected_label

        if st.session_state.lat is None or st.session_state.lon is None:
            st.error("Select location or click on map ❌")

        else:
            try:
                aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={st.session_state.lat}&lon={st.session_state.lon}&appid={API_KEY}"
                data = requests.get(aqi_url).json()

                if "list" in data:
                    st.session_state.aqi_data = data
                else:
                    st.error("Failed to fetch AQI ❌")

            except:
                st.error("API Error ❌")

with col2:
    if st.button("🔄 Refresh"):
        st.session_state.aqi_data = None
        st.session_state.lat = None
        st.session_state.lon = None
        st.rerun()

# ---------------- AQI DISPLAY ----------------
if st.session_state.aqi_data:

    data = st.session_state.aqi_data
    aqi = data["list"][0]["main"]["aqi"]
    components = data["list"][0]["components"]

    category, color = get_aqi_info(aqi)
    aqi_range = get_aqi_range(aqi)

    st.markdown(f"""
    <div style="
        background:{color};
        padding:20px;
        border-radius:12px;
        color:black;
        text-align:center;
    ">

    <div style="
        
        top:10px;
        left:15px;
        background:white;
        padding:6px 14px;
        border-radius:12px;
        font-weight:bold;
        font-size:30px;
    ">
        AQI value lies between: {aqi_range}
    </div>

    <h2>{st.session_state.city_input.upper()}</h2>
    <h1>AQI Category: {aqi}</h1>
    <h3>{category}</h3>

    </div>
    """, unsafe_allow_html=True)

    st.progress(aqi / 5)

    st.markdown("### 🧪 Pollutants")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("PM2.5", round(components["pm2_5"], 2))
        st.metric("PM10", round(components["pm10"], 2))
        st.metric("CO", round(components["co"], 2))
        st.metric("NO2", round(components["no2"], 2))

    with c2:
        st.metric("O3", round(components["o3"], 2))
        st.metric("SO2", round(components["so2"], 2))
        st.metric("NH3", round(components["nh3"], 2))

# ---------------- MAP ----------------
st.markdown("### 🗺️ Click Anywhere on Map")

if st.session_state.lat is not None and st.session_state.lon is not None:
    center = [st.session_state.lat, st.session_state.lon]
    zoom = 5
else:
    center = [20, 0]
    zoom = 2

m = folium.Map(
    location=center,
    zoom_start=zoom,
    tiles="CartoDB positron",
    max_bounds=True
)

# Marker
if st.session_state.lat is not None and st.session_state.lon is not None:
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Selected Location",
        icon=folium.Icon(color="red")
    ).add_to(m)

# Render map
map_data = st_folium(
    m,
    height=550,
    use_container_width=True,
    returned_objects=["last_clicked"]
)

# ---------------- MAP CLICK ----------------
if map_data and map_data.get("last_clicked"):

    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    if st.session_state.lat != lat or st.session_state.lon != lon:

        st.session_state.lat = lat
        st.session_state.lon = lon

        try:
            reverse_url = f"https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
            res = requests.get(reverse_url).json()

            if isinstance(res, list) and len(res) > 0:
                place = res[0]

                name = place.get("name", "")
                state = place.get("state", "")
                country = place.get("country", "")

                place_name = f"{name}, {state}, {country}".replace(" ,", "").replace(",,", ",")

                st.session_state.city_input = place_name
                st.session_state.city_box = place_name

            else:
                coords = f"{lat:.4f}, {lon:.4f}"
                st.session_state.city_input = coords
                st.session_state.city_box = coords

        except:
            coords = f"{lat:.4f}, {lon:.4f}"
            st.session_state.city_input = coords
            st.session_state.city_box = coords

        st.rerun()