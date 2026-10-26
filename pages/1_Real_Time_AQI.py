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
defaults = {
    "city_input": "Delhi",
    "lat": None,
    "lon": None,
    "aqi_data": None,
    "last_click": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

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

def fetch_aqi(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        data = requests.get(url).json()
        if "list" in data:
            st.session_state.aqi_data = data
    except:
        pass
# ---------------- AUTO SEARCH ON ENTER ----------------
def search_city_and_fetch():
    st.session_state.pop("map_selected_location", None)
    query = st.session_state.city_search.strip()

    if not query:
        st.session_state.aqi_data = None
        return

    try:
        geo_url = "https://api.openweathermap.org/geo/1.0/direct"

        response = requests.get(
            geo_url,
            params={
                "q": query,
                "limit": 5,
                "appid": API_KEY
            },
            timeout=15
        )

        response.raise_for_status()
        locations = response.json()

        if isinstance(locations, list) and locations:
            # Automatically select the first matching city
            place = locations[0]

            lat = place["lat"]
            lon = place["lon"]

            name = place.get("name", "")
            state = place.get("state", "")
            country = place.get("country", "")

            full_location = ", ".join(
                x for x in [name, state, country] if x
            )

            st.session_state.city_input = full_location
            st.session_state.lat = lat
            st.session_state.lon = lon

            # Automatically retrieve AQI
            fetch_aqi(lat, lon)

        else:
            st.session_state.aqi_data = None
            st.warning("No matching city found.")

    except requests.exceptions.RequestException as error:
        st.error(f"Unable to search city: {error}")
# ---------------- INPUT ----------------
if "city_search" not in st.session_state:
    st.session_state.city_search = st.session_state.city_input

pending_label = st.session_state.pop(
    "pending_map_label", None
)

if pending_label is not None:
    st.session_state.city_search = pending_label

city_input = st.text_input(
    "🏙️ Enter City Name",
    key="city_search",
    placeholder="Enter city and press Enter",
    on_change=search_city_and_fetch
)
selected_location = None
selected_label = ""

# ---------------- CITY SEARCH ----------------

selected_location = None
selected_label = ""
options = []

# Check whether the user selected a location through the map
map_location = st.session_state.get("map_selected_location")

# CASE 1: Location selected by clicking on the map
if (
    map_location is not None
    and city_input.strip() == map_location["label"]
):

    # Preserve the exact coordinates selected on the map
    options.append((
        map_location["label"],
        map_location
    ))

# CASE 2: Location entered manually in the search box
elif city_input.strip():

    try:
        geo_url = "https://api.openweathermap.org/geo/1.0/direct"

        response = requests.get(
            geo_url,
            params={
                "q": city_input,
                "limit": 5,
                "appid": API_KEY
            },
            timeout=15
        )

        response.raise_for_status()
        geo_response = response.json()

        if isinstance(geo_response, list) and len(geo_response) > 0:

            for loc in geo_response:

                name = loc.get("name", "")
                state = loc.get("state", "")
                country = loc.get("country", "")

                # Create a readable location name
                label = ", ".join(
                    part for part in [name, state, country] if part
                )

                options.append((label, loc))

    except requests.exceptions.RequestException as error:
        st.warning(f"Unable to search location: {error}")

# ---------------- LOCATION DROPDOWN ----------------

if options:

    selected_label = st.selectbox(
        "📍 Select Location",
        options=[item[0] for item in options]
    )

    # Retrieve the coordinates for the selected location
    for label, loc in options:

        if label == selected_label:

            selected_location = loc
            break

elif city_input.strip():

    st.info(
        "No matching location found. "
        "Try another city or select a location on the map."
    )

# ---------------- BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Get AQI"):

        if selected_location:
            st.session_state.lat = selected_location["lat"]
            st.session_state.lon = selected_location["lon"]
            st.session_state.city_input = selected_label

        if st.session_state.lat is None:
            st.error("Select location or click on map ❌")
        else:
            fetch_aqi(st.session_state.lat, st.session_state.lon)

with col2:
    if st.button("🔄 Refresh"):
        st.session_state.city_input = "Delhi"
        st.session_state.lat = None
        st.session_state.lon = None
        st.session_state.aqi_data = None
        st.session_state.last_click = None
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
        padding:25px 20px;
        border-radius:18px;
        color:black;
        text-align:center;
        margin-top:10px;
        box-shadow:0 6px 18px rgba(0,0,0,0.15);
    ">

    <div style="
        background:white;
        padding:10px;
        border-radius:12px;
        font-weight:700;
        font-size:20px;
        margin-bottom:18px;
    ">
        AQI Value Lies Between: {aqi_range}
    </div>

    <div style="
        font-size:22px;
        font-weight:700;
        margin-bottom:12px;
        word-wrap:break-word;
    ">
        {st.session_state.city_input.upper()}
    </div>

    <div style="
        font-size:42px;
        font-weight:900;
        margin-bottom:10px;
    ">
        AQI Category: {aqi}
    </div>

    <div style="
        font-size:30px;
        font-weight:700;
    ">
        {category}
    </div>

    </div>
    """, unsafe_allow_html=True)

    st.progress(aqi / 5)

    st.markdown("## 🧪 Pollutants")

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

if st.session_state.lat is not None:
    center = [st.session_state.lat, st.session_state.lon]
    zoom = 5
else:
    center = [20, 0]
    zoom = 2

m = folium.Map(
    location=center,
    zoom_start=zoom,
    tiles=None
)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles © Esri — Source: Esri and contributors",
    name="Esri World Street Map",
    overlay=False,
    control=True,
    max_zoom=19
).add_to(m)

if st.session_state.lat is not None:
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Selected Location",
        icon=folium.Icon(color="red")
    ).add_to(m)

map_data = st_folium(
    m,
    height=550,
    use_container_width=True,
    returned_objects=["last_clicked"]
)

# ---------------- MAP CLICK ----------------
if map_data and map_data.get("last_clicked"):

    lat = round(map_data["last_clicked"]["lat"], 4)
    lon = round(map_data["last_clicked"]["lng"], 4)

    current_click = (lat, lon)

    # prevents double click same place error
    if current_click != st.session_state.last_click:

        st.session_state.last_click = current_click
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

                full_location = ", ".join(
                    x for x in [name, state, country] if x
                )

                if full_location.strip():
                    st.session_state.city_input = full_location
                else:
                    st.session_state.city_input = f"{lat}, {lon}"

            else:
                st.session_state.city_input = f"{lat}, {lon}"

        except:
            st.session_state.city_input = f"{lat}, {lon}"

        fetch_aqi(lat, lon)
        st.session_state.map_selected_location = {
            "label": st.session_state.city_input,
            "lat": lat,
            "lon": lon
        }


        st.session_state.pending_map_label = (
            st.session_state.city_input
        )

        st.rerun()