
 

import streamlit as st

import sqlite3

import json

import uuid

import math

from pathlib import Path

from datetime import date, timedelta

 

import folium

from streamlit_folium import st_folium

from geopy.geocoders import Nominatim

from geopy.extra.rate_limiter import RateLimiter

 

# ==================================================

# KONFIGURATION

# ==================================================

 

st.set_page_config(

    page_title="ShareTool – Teilen statt kaufen",

    page_icon="🛠️",

    layout="wide"

)

 

DB_FILE = "sharetool.db"

IMAGE_DIR = Path("sharetool_images")

IMAGE_DIR.mkdir(exist_ok=True)

 

# Ungefährer Mittelpunkt von Ulm als Startposition

DEFAULT_LAT = 48.3984

DEFAULT_LON = 9.9916

 

CATEGORIES = {

    "Gartengeräte": {

        "icon": "🌿",

        "description": "Rasenmäher, Heckenscheren und mehr",

        "image": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=900&q=80"

    },

    "Werkzeuge": {

        "icon": "🔧",

        "description": "Bohrmaschinen, Sägen und Werkzeug",

        "image": https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=900&q=80

    },

    "Haushalt & Reinigung": {

        "icon": "🧹",

        "description": "Staubsauger und Reinigungsgeräte",

        "image": https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=80

    },

    "Bau & Renovierung": {

        "icon": "🏠",

        "description": "Alles für dein nächstes Projekt",

        "image": https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=900&q=80

    },

    "Autowerkzeug": {

        "icon": "🚗",

        "description": "Wagenheber, Ladegeräte und Zubehör",

        "image": https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=900&q=80

    },

    "Transport & Leiter": {

        "icon": "🛒",

        "description": "Leitern und Transporthilfen",

        "image": https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?auto=format&fit=crop&w=900&q=80

    },

    "Küche & Haushalt": {

        "icon": "🍳",

        "description": "Küchengeräte und praktische Helfer",

        "image": https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80

    },

    "Freizeit & Outdoor": {

        "icon": "🏕️",

        "description": "Camping, Sport und Outdoor",

        "image": https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?auto=format&fit=crop&w=900&q=80

    },

    "Elektronik & Technik": {

        "icon": "💻",

        "description": "Technik und Elektronik",

        "image": https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80

    },

    "Event & Party": {

        "icon": "🎉",

        "description": "Musik, Beleuchtung und Partyzubehör",

        "image": https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=900&q=80

    },

    "Gartenpflege & Außenbereich": {

        "icon": "🍃",

        "description": "Pflanzen, Gartenpflege und Außenbereich",

        "image": https://images.unsplash.com/photo-1599685315640-200a9f6e5e1e?auto=format&fit=crop&w=900&q=80

    },

    "Sonstiges": {

        "icon": "📦",

        "description": "Alles, was sonst geteilt werden kann",

        "image": https://images.unsplash.com/photo-1581147036324-c17ac41feb19?auto=format&fit=crop&w=900&q=80

    }

}

 

# ==================================================

# DATENBANK UND MIGRATIONEN

# ==================================================

 

def get_connection():

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)

    conn.row_factory = sqlite3.Row

    return conn

 

 

def init_database():

    conn = get_connection()

    cur = conn.cursor()

 

    cur.execute("""

        CREATE TABLE IF NOT EXISTS tools (

            id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            category TEXT NOT NULL,

            description TEXT,

            price REAL DEFAULT 0,

            location TEXT,

            owner TEXT,

            image_urls TEXT DEFAULT '[]',

            created_at TEXT,

            latitude REAL,

            longitude REAL

        )

    """)

 

    cur.execute("""

        CREATE TABLE IF NOT EXISTS bookings (

            id TEXT PRIMARY KEY,

            tool_id TEXT NOT NULL,

            renter TEXT NOT NULL,

            start_date TEXT NOT NULL,

            end_date TEXT NOT NULL,

            message TEXT,

            status TEXT DEFAULT 'Angefragt',

            created_at TEXT

        )

    """)

 

    columns = {

        row["name"]

        for row in cur.execute("PRAGMA table_info(tools)").fetchall()

    }

 

    migrations = {

        "image_urls": "TEXT DEFAULT '[]'",

        "created_at": "TEXT",

        "latitude": "REAL",

        "longitude": "REAL"

    }

 

    for column, definition in migrations.items():

        if column not in columns:

            cur.execute(

                f"ALTER TABLE tools ADD COLUMN {column} {definition}"

            )

 

    conn.commit()

    conn.close()

 

 

def seed_example_tools():

    conn = get_connection()

 

    count = conn.execute(

        "SELECT COUNT(*) FROM tools"

    ).fetchone()[0]

 

    if count == 0:

        examples = [

            (

                "Akku-Bohrmaschine", "Werkzeuge",

                "Akku-Bohrmaschine für Reparaturen.",

                8, "Ulm", "Max", 48.3984, 9.9916

            ),

            (

                "Elektrischer Rasenmäher", "Gartengeräte",

                "Rasenmäher für kleine und mittlere Gärten.",

                15, "Neu-Ulm", "Lisa", 48.3933, 9.9990

            ),

            (

                "Hochdruckreiniger", "Haushalt & Reinigung",

                "Für Terrasse, Gartenmöbel und Einfahrt.",

                12, "Blaustein", "Thomas", 48.4120, 9.9160

            ),

            (

                "Teleskop-Leiter", "Transport & Leiter",

                "Ausziehbare Leiter für Arbeiten am Haus.",

                7, "Ulm", "Sarah", 48.4100, 9.9800

            ),

            (

                "Campingzelt", "Freizeit & Outdoor",

                "Zelt für Wochenendausflüge.",

                10, "Erbach", "Jonas", 48.3280, 9.8870

            ),

            (

                "Exzenterschleifer", "Bau & Renovierung",

                "Schleifgerät für Holz und Renovierung.",

                9, "Ulm", "Miriam", 48.3850, 9.9700

            )

        ]

 

        for item in examples:

            name, category, desc, price, location, owner, lat, lon = item

 

            conn.execute("""

                INSERT INTO tools (

                    id, name, category, description, price,

                    location, owner, image_urls, created_at,

                    latitude, longitude

                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """, (

                str(uuid.uuid4()), name, category, desc, price,

                location, owner, "[]", date.today().isoformat(),

                lat, lon

            ))

 

    conn.commit()

    conn.close()

 

 

init_database()

seed_example_tools()

 

# ==================================================

# HILFSFUNKTIONEN

# ==================================================

 

def get_all_tools():

    conn = get_connection()

    rows = conn.execute(

        "SELECT * FROM tools ORDER BY created_at DESC"

    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]

 

 

def get_tool(tool_id):

    conn = get_connection()

    row = conn.execute(

        "SELECT * FROM tools WHERE id = ?",

        (tool_id,)

    ).fetchone()

    conn.close()

    return dict(row) if row else None

 

 

def get_images(tool):

    try:

        result = json.loads(tool.get("image_urls") or "[]")

        return result if isinstance(result, list) else []

    except (ValueError, TypeError):

        return []

 

 

def save_images(files):

    paths = []

 

    for file in files or []:

        suffix = Path(file.name).suffix.lower()

 

        if suffix not in (".jpg", ".jpeg", ".png", ".webp"):

            continue

 

        filename = f"{uuid.uuid4().hex}{suffix}"

        path = IMAGE_DIR / filename

        path.write_bytes(file.getvalue())

        paths.append(str(path))

 

    return paths

 

 

def geocode_address(address):

    """Adresse nur bei ausdrücklicher Aktion des Nutzers suchen."""

    try:

        geolocator = Nominatim(

            user_agent="ShareTool_Local_Sharing_App"

        )

        geocode = RateLimiter(

            geolocator.geocode,

            min_delay_seconds=1,

            swallow_exceptions=True

        )

        result = geocode(address, timeout=10)

 

        if result:

            return float(result.latitude), float(result.longitude)

 

    except Exception:

        pass

 

    return None, None

 

 

def distance_km(lat1, lon1, lat2, lon2):

    """Luftlinienentfernung zwischen zwei Koordinaten."""

    radius = 6371.0

 

    lat1 = math.radians(float(lat1))

    lon1 = math.radians(float(lon1))

    lat2 = math.radians(float(lat2))

    lon2 = math.radians(float(lon2))

 

    dlat = lat2 - lat1

    dlon = lon2 - lon1

 

    a = (

        math.sin(dlat / 2) ** 2

        + math.cos(lat1) * math.cos(lat2)

        * math.sin(dlon / 2) ** 2

    )

 

    return radius * 2 * math.atan2(

        math.sqrt(a),

        math.sqrt(max(0, 1 - a))

    )

 

 

def add_tool_to_database(

    name, category, description, price, location,

    owner, image_paths, latitude, longitude

):

    conn = get_connection()

 

    conn.execute("""

        INSERT INTO tools (

            id, name, category, description, price,

            location, owner, image_urls, created_at,

            latitude, longitude

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        str(uuid.uuid4()),

        name.strip(),

        category,

        description.strip(),

        float(price),

        location.strip(),

        owner.strip(),

        json.dumps(image_paths),

        date.today().isoformat(),

        latitude,

        longitude

    ))

 

    conn.commit()

    conn.close()

 

 

def create_booking(tool_id, renter, start_date, end_date, message):

    conn = get_connection()

 

    conn.execute("""

        INSERT INTO bookings (

            id, tool_id, renter, start_date, end_date,

            message, status, created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        str(uuid.uuid4()), tool_id, renter.strip(),

        start_date.isoformat(), end_date.isoformat(),

        message.strip(), "Angefragt", date.today().isoformat()

    ))

 

    conn.commit()

    conn.close()

 

 

def get_bookings():

    conn = get_connection()

 

    rows = conn.execute("""

        SELECT bookings.*, tools.name AS tool_name,

               tools.location AS tool_location

        FROM bookings

        LEFT JOIN tools ON bookings.tool_id = tools.id

        ORDER BY bookings.created_at DESC

    """).fetchall()

 

    conn.close()

    return [dict(row) for row in rows]

 

 

def show_tool_card(tool):

    with st.container(border=True):

        images = [

            p for p in get_images(tool)

            if Path(p).exists()

        ]

 

        if images:

            st.image(images[0], use_container_width=True)

        else:

            category_info = CATEGORIES.get(

                tool["category"], CATEGORIES["Sonstiges"]

            )

            st.image(

                category_info["image"],

                use_container_width=True

            )

 

        st.subheader(tool["name"])

        st.caption(

            f'{tool["category"]} · 📍 {tool.get("location") or "Ort unbekannt"}'

        )

        st.write(tool.get("description") or "Keine Beschreibung")

        st.markdown(

            f'**{float(tool.get("price") or 0):.2f} € pro Tag**'

        )

        st.caption(f'Anbieter: {tool.get("owner") or "Unbekannt"}')

 

        if st.button(

            "Details & reservieren",

            key=f"details_{tool['id']}",

            use_container_width=True

        ):

            st.session_state["selected_tool_id"] = tool["id"]

            st.session_state["page"] = "details"

            st.rerun()

 

 

# ==================================================

# DESIGN

# ==================================================

 

st.markdown("""

<style>

    .stApp { background-color: #f6f8f5; }

    h1, h2, h3 { color: #244c36; }

    .hero {

        background: linear-gradient(120deg, #204d35, #4d8960);

        padding: 30px;

        border-radius: 18px;

        color: white;

        margin-bottom: 22px;

    }

    .hero h1 { color: white; }

</style>

""", unsafe_allow_html=True)

 

# ==================================================

# NAVIGATION

# ==================================================

 

if "page" not in st.session_state:

    st.session_state.page = "home"

 

if "selected_category" not in st.session_state:

    st.session_state.selected_category = None

 

if "selected_tool_id" not in st.session_state:

    st.session_state.selected_tool_id = None

 

if "map_center" not in st.session_state:

    st.session_state.map_center = [DEFAULT_LAT, DEFAULT_LON]

 

if "new_marker" not in st.session_state:

    st.session_state.new_marker = [DEFAULT_LAT, DEFAULT_LON]

 

with st.sidebar:

    st.title("🛠️ ShareTool")

    st.caption("Teilen statt kaufen")

    st.divider()

 

    if st.button("🏡 Startseite", use_container_width=True):

        st.session_state.page = "home"

        st.rerun()

 

    if st.button("🗺️ Karte entdecken", use_container_width=True):

        st.session_state.page = "map"

        st.rerun()

 

    if st.button("➕ Gerät anbieten", use_container_width=True):

        st.session_state.page = "add"

        st.rerun()

 

    if st.button("📅 Reservierungen", use_container_width=True):

        st.session_state.page = "bookings"

        st.rerun()

 

    st.divider()

    st.caption("Gemeinsam nutzen. Ressourcen sparen.")

 

tools = get_all_tools()

 

# ==================================================

# STARTSEITE MIT KATEGORIEN

# ==================================================

 

if st.session_state.page == "home":

 

    st.markdown("""

    <div class="hero">

        <h1>ShareTool – Teilen statt kaufen 🛠️</h1>

        <p>Finde Geräte in deiner Umgebung oder teile deine eigenen.</p>

    </div>

    """, unsafe_allow_html=True)

 

    c1, c2, c3 = st.columns(3)

 

    c1.metric("Geräte im Angebot", len(tools))

    c2.metric("Kategorien", len(CATEGORIES))

    c3.metric(

        "Standorte",

        len(set(t.get("location") for t in tools if t.get("location")))

    )

 

    st.subheader("🔎 Gerät suchen")

 

    query = st.text_input(

        "Suche nach Gerät, Kategorie oder Ort",

        placeholder="z. B. Bohrmaschine, Garten, Ulm"

    )

 

    if query.strip():

        q = query.lower().strip()

 

        results = [

            t for t in tools

            if q in str(t.get("name", "")).lower()

            or q in str(t.get("category", "")).lower()

            or q in str(t.get("description", "")).lower()

            or q in str(t.get("location", "")).lower()

        ]

 

        st.subheader(f"Suchergebnisse: {len(results)}")

 

        if results:

            cols = st.columns(3)

            for i, tool in enumerate(results):

                with cols[i % 3]:

                    show_tool_card(tool)

        else:

            st.info("Keine passenden Geräte gefunden.")

 

    st.subheader("🧰 Kategorien entdecken")

 

    names = list(CATEGORIES.keys())

 

    for start in range(0, len(names), 4):

        row_names = names[start:start + 4]

        cols = st.columns(4)

 

        for col, category in zip(cols, row_names):

            info = CATEGORIES[category]

 

            with col:

                with st.container(border=True):

                    st.image(info["image"], use_container_width=True)

                    st.markdown(f"### {info['icon']} {category}")

                    st.caption(info["description"])

 

                    count = sum(

                        1 for t in tools if t["category"] == category

                    )

                    st.caption(f"{count} Geräte")

 

                    if st.button(

                        "Kategorie öffnen",

                        key=f"cat_{category}",

                        use_container_width=True

                    ):

                        st.session_state.selected_category = category

                        st.session_state.page = "category"

                        st.rerun()

 

    st.divider()

    st.subheader("✨ Neu eingestellte Geräte")

 

    if tools:

        cols = st.columns(3)

        for i, tool in enumerate(tools[:3]):

            with cols[i]:

                show_tool_card(tool)

    else:

        st.info("Noch keine Geräte vorhanden.")

 

# ==================================================

# KATEGORIE

# ==================================================

 

elif st.session_state.page == "category":

 

    category = st.session_state.selected_category

 

    if category not in CATEGORIES:

        st.session_state.page = "home"

        st.rerun()

 

    st.title(

        f'{CATEGORIES[category]["icon"]} {category}'

    )

    st.write(CATEGORIES[category]["description"])

 

    if st.button("← Zurück zur Startseite"):

        st.session_state.page = "home"

        st.rerun()

 

    selected = [t for t in tools if t["category"] == category]

 

    if selected:

        cols = st.columns(3)

        for i, tool in enumerate(selected):

            with cols[i % 3]:

                show_tool_card(tool)

    else:

        st.info("In dieser Kategorie gibt es noch keine Geräte.")

 

# ==================================================

# INTERAKTIVE KARTE

# ==================================================

 

elif st.session_state.page == "map":

 

    st.title("🗺️ Geräte in deiner Umgebung")

    st.write(

        "Entdecke verfügbare Geräte auf der Karte. "

        "Wähle eine Markierung aus, um mehr zu erfahren."

    )

 

    col1, col2 = st.columns([2, 1])

 

    with col1:

        map_search = st.text_input(

            "Ort für die Karte",

            value="Ulm",

            key="map_search"

        )

 

    with col2:

        radius = st.selectbox(

            "Umkreis",

            [5, 10, 25, 50, 100],

            index=2,

            format_func=lambda x: f"{x} km"

        )

 

    if st.button("Ort auf der Karte suchen"):

        lat, lon = geocode_address(map_search)

 

        if lat is not None:

            st.session_state.map_center = [lat, lon]

            st.success("Ort gefunden.")

        else:

            st.warning(

                "Der Ort konnte nicht gefunden werden. "

                "Bitte versuche eine genauere Adresse."

            )

 

    map_category = st.selectbox(

        "Kategorie filtern",

        ["Alle Kategorien"] + list(CATEGORIES.keys())

    )

 

    center_lat, center_lon = st.session_state.map_center

 

    nearby_tools = []

 

    for tool in tools:

        lat = tool.get("latitude")

        lon = tool.get("longitude")

 

        if lat is None or lon is None:

            continue

 

        if map_category != "Alle Kategorien":

            if tool["category"] != map_category:

                continue

 

        distance = distance_km(

            center_lat, center_lon, lat, lon

        )

 

        if distance <= radius:

            tool["distance_km"] = distance

            nearby_tools.append(tool)

 

    st.caption(

        f"{len(nearby_tools)} Geräte im Umkreis von {radius} km"

    )

 

    map_obj = folium.Map(

        location=[center_lat, center_lon],

        zoom_start=12,

        control_scale=True

    )

 

    folium.Marker(

        [center_lat, center_lon],

        tooltip="Gesuchter Ort",

        popup="Mittelpunkt der Suche",

        icon=folium.Icon(color="blue", icon="home")

    ).add_to(map_obj)

 

    for tool in nearby_tools:

        lat = float(tool["latitude"])

        lon = float(tool["longitude"])

 

        popup_html = f"""

        <div style="width:210px">

            <b>{tool['name']}</b><br>

            {tool['category']}<br>

            {float(tool.get('price') or 0):.2f} € pro Tag<br>

            📍 {tool.get('location') or ''}<br>

            Anbieter: {tool.get('owner') or 'Unbekannt'}

        </div>

        """

 

        color = "green"

 

        folium.Marker(

            location=[lat, lon],

            tooltip=tool["name"],

            popup=folium.Popup(popup_html, max_width=260),

            icon=folium.Icon(

                color=color,

                icon="wrench",

                prefix="fa"

            )

        ).add_to(map_obj)

 

    folium.LayerControl().add_to(map_obj)

 

    map_result = st_folium(

        map_obj,

        height=580,

        use_container_width=True,

        key="sharetool_main_map"

    )

 

    st.caption(

        "Kartendaten © OpenStreetMap-Mitwirkende. "

        "Die Karte benötigt eine Internetverbindung."

    )

 

    if nearby_tools:

        st.subheader("Geräte auf der Karte")

 

        cols = st.columns(3)

 

        for i, tool in enumerate(nearby_tools):

            with cols[i % 3]:

                show_tool_card(tool)

                st.caption(

                    f'Ungefähr {tool["distance_km"]:.1f} km entfernt'

                )

    else:

        st.info(

            "Keine Geräte in diesem Umkreis gefunden. "

            "Vergrößere den Umkreis oder wähle eine andere Kategorie."

        )

 

# ==================================================

# GERÄTEDETAILS UND RESERVIERUNG

# ==================================================

 

elif st.session_state.page == "details":

 

    tool = get_tool(st.session_state.selected_tool_id)

 

    if not tool:

        st.error("Gerät nicht gefunden.")

    else:

        if st.button("← Zurück"):

            st.session_state.page = "home"

            st.rerun()

 

        st.title(tool["name"])

 

        left, right = st.columns(2)

 

        with left:

            images = [

                p for p in get_images(tool)

                if Path(p).exists()

            ]

 

            if images:

                st.image(images, use_container_width=True)

            else:

                st.image(

                    CATEGORIES.get(

                        tool["category"], CATEGORIES["Sonstiges"]

                    )["image"],

                    use_container_width=True

                )

 

        with right:

            st.subheader(tool["category"])

            st.markdown(

                f'## {float(tool.get("price") or 0):.2f} € pro Tag'

            )

            st.write(tool.get("description") or "Keine Beschreibung")

            st.write(f'📍 Standort: {tool.get("location") or "Unbekannt"}')

            st.write(f'👤 Anbieter: {tool.get("owner") or "Unbekannt"}')

 

            if (

                tool.get("latitude") is not None

                and tool.get("longitude") is not None

            ):

                detail_map = folium.Map(

                    location=[

                        tool["latitude"], tool["longitude"]

                    ],

                    zoom_start=15

                )

 

                folium.Marker(

                    [tool["latitude"], tool["longitude"]],

                    tooltip=tool["name"]

                ).add_to(detail_map)

 

                st_folium(

                    detail_map,

                    height=250,

                    use_container_width=True,

                    key=f"detail_map_{tool['id']}"

                )

 

        st.divider()

        st.subheader("📅 Reservierung anfragen")

 

        with st.form("booking_form"):

            renter = st.text_input("Dein Name")

 

            start_date = st.date_input(

                "Von",

                value=date.today() + timedelta(days=1),

                min_value=date.today()

            )

 

            end_date = st.date_input(

                "Bis",

                value=date.today() + timedelta(days=2),

                min_value=date.today()

            )

 

            message = st.text_area(

                "Nachricht an den Anbieter (optional)"

            )

 

            submitted = st.form_submit_button(

                "Reservierungsanfrage senden"

            )

 

            if submitted:

                if not renter.strip():

                    st.error("Bitte gib deinen Namen ein.")

                elif end_date < start_date:

                    st.error("Das Enddatum darf nicht vor dem Startdatum liegen.")

                else:

                    create_booking(

                        tool["id"], renter,

                        start_date, end_date, message

                    )

                    st.success("Reservierungsanfrage gespeichert!")

 

# ==================================================

# NEUES GERÄT ANBIETEN

# ==================================================

 

elif st.session_state.page == "add":

 

    st.title("➕ Gerät anbieten")

    st.write(

        "Trage dein Gerät ein und lege seinen Standort auf der Karte fest."

    )

 

    with st.form("new_tool_form"):

 

        name = st.text_input("Name des Geräts *")

 

        category = st.selectbox(

            "Kategorie *",

            list(CATEGORIES.keys())

        )

 

        description = st.text_area("Beschreibung")

 

        price = st.number_input(

            "Preis pro Tag (€)",

            min_value=0.0,

            value=5.0,

            step=0.5

        )

 

        location = st.text_input(

            "Adresse oder Ort *",

            placeholder="z. B. Musterstraße 1, Ulm"

        )

 

        owner = st.text_input("Dein Name *")

 

        uploaded_files = st.file_uploader(

            "Gerätefotos",

            type=["jpg", "jpeg", "png", "webp"],

            accept_multiple_files=True

        )

 

        find_location = st.form_submit_button(

            "Adresse auf der Karte finden"

        )

 

    if find_location:

        if location.strip():

            lat, lon = geocode_address(location.strip())

 

            if lat is not None:

                st.session_state.new_marker = [lat, lon]

                st.success(

                    "Standort gefunden. Du kannst die Markierung unten korrigieren."

                )

            else:

                st.error(

                    "Adresse nicht gefunden. Bitte gib eine genauere Adresse ein."

                )

        else:

            st.warning("Bitte zuerst eine Adresse eingeben.")

 

    st.subheader("📍 Position auf der Karte festlegen")

    st.write(

        "Klicke auf die Karte, um den Standort festzulegen. "

        "Die Markierung wird beim nächsten Neuzeichnen aktualisiert."

    )

 

    marker_lat, marker_lon = st.session_state.new_marker

 

    edit_map = folium.Map(

        location=[marker_lat, marker_lon],

        zoom_start=14,

        control_scale=True

    )

 

    folium.Marker(

        [marker_lat, marker_lon],

        tooltip="Gerätestandort",

        icon=folium.Icon(color="green", icon="wrench")

    ).add_to(edit_map)

 

    click_result = st_folium(

        edit_map,

        height=400,

        use_container_width=True,

        key="new_tool_location_map"

    )

 

    if click_result and click_result.get("last_clicked"):

        clicked = click_result["last_clicked"]

        new_lat = float(clicked["lat"])

        new_lon = float(clicked["lng"])

 

        old = st.session_state.new_marker

 

        if (

            abs(new_lat - old[0]) > 0.00001

            or abs(new_lon - old[1]) > 0.00001

        ):

            st.session_state.new_marker = [new_lat, new_lon]

            st.rerun()

 

    st.info(

        f"Ausgewählte Koordinaten: "

        f"{st.session_state.new_marker[0]:.6f}, "

        f"{st.session_state.new_marker[1]:.6f}"

    )

 

    if st.button("Gerät veröffentlichen", use_container_width=True):

 

        if not name.strip():

            st.error("Bitte gib einen Gerätenamen ein.")

        elif not location.strip():

            st.error("Bitte gib einen Standort ein.")

        elif not owner.strip():

            st.error("Bitte gib deinen Namen ein.")

        else:

            image_paths = save_images(uploaded_files)

 

            lat, lon = st.session_state.new_marker

 

            add_tool_to_database(

                name,

                category,

                description,

                price,

                location,

                owner,

                image_paths,

                lat,

                lon

            )

 

            st.success(f"„{name}“ wurde veröffentlicht!")

            st.session_state.new_marker = [

                DEFAULT_LAT, DEFAULT_LON

            ]

            st.session_state.page = "home"

            st.rerun()

 

# ==================================================

# RESERVIERUNGEN VERWALTEN

# ==================================================

 

elif st.session_state.page == "bookings":

 

    st.title("📅 Reservierungen")

 

    bookings = get_bookings()

 

    if not bookings:

        st.info("Noch keine Reservierungsanfragen vorhanden.")

 

    for booking in bookings:

        with st.container(border=True):

 

            st.subheader(

                booking.get("tool_name") or "Gerät nicht verfügbar"

            )

 

            st.write(f'Anfragende Person: {booking["renter"]}')

            st.write(

                f'Zeitraum: {booking["start_date"]} bis {booking["end_date"]}'

            )

            st.write(

                f'Standort: {booking.get("tool_location") or "Unbekannt"}'

            )

 

            if booking.get("message"):

                st.write(f'Nachricht: {booking["message"]}')

 

            statuses = [

                "Angefragt",

                "Bestätigt",

                "Abgelehnt",

                "Abgeschlossen"

            ]

 

            current = booking.get("status", "Angefragt")

 

            if current not in statuses:

                current = "Angefragt"

 

            new_status = st.selectbox(

                "Status",

                statuses,

                index=statuses.index(current),

                key=f"status_{booking['id']}"

            )

 

            if st.button(

                "Status speichern",

                key=f"save_{booking['id']}"

            ):

                conn = get_connection()

 

                conn.execute(

                    "UPDATE bookings SET status = ? WHERE id = ?",

                    (new_status, booking["id"])

                )

 

                conn.commit()

                conn.close()

 

                st.success("Status aktualisiert.")

                st.rerun()

 

# ==================================================

# FOOTER

# ==================================================

 

st.divider()

 

st.caption(

    "ShareTool · Teilen statt kaufen · Gemeinsam Ressourcen sparen 🌱"

)

 

