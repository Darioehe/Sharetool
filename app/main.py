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

        "image": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format

" 
...