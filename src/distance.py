#!/usr/bin/env python3

import json
import math
import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.config import (
    DISTANCE_CACHE_FILE,
    DISTANCE_LEGACY_JSON_CACHE_FILE,
    DISTANCE_MAX_UNCACHED_ELEMENTS_PER_RUN,
    DISTANCE_REQUEST_DELAY_SECONDS,
    DISTANCE_USER_AGENT,
    GOOGLE_MAPS_API_KEY_ENV,
    OPENROUTESERVICE_API_KEY_ENV
)
from src.env import load_dotenv


load_dotenv()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
UNCACHED_ELEMENTS_USED = 0
LAST_FREE_REQUEST_AT = 0.0

STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"
}

STATE_CENTERS = {
    "AL": (32.806671, -86.791130),
    "AK": (61.370716, -152.404419),
    "AZ": (33.729759, -111.431221),
    "AR": (34.969704, -92.373123),
    "CA": (36.116203, -119.681564),
    "CO": (39.059811, -105.311104),
    "CT": (41.597782, -72.755371),
    "DE": (39.318523, -75.507141),
    "DC": (38.897438, -77.026817),
    "FL": (27.766279, -81.686783),
    "GA": (33.040619, -83.643074),
    "HI": (21.094318, -157.498337),
    "ID": (44.240459, -114.478828),
    "IL": (40.349457, -88.986137),
    "IN": (39.849426, -86.258278),
    "IA": (42.011539, -93.210526),
    "KS": (38.526600, -96.726486),
    "KY": (37.668140, -84.670067),
    "LA": (31.169546, -91.867805),
    "ME": (44.693947, -69.381927),
    "MD": (39.063946, -76.802101),
    "MA": (42.230171, -71.530106),
    "MI": (43.326618, -84.536095),
    "MN": (45.694454, -93.900192),
    "MS": (32.741646, -89.678696),
    "MO": (38.456085, -92.288368),
    "MT": (46.921925, -110.454353),
    "NE": (41.125370, -98.268082),
    "NV": (38.313515, -117.055374),
    "NH": (43.452492, -71.563896),
    "NJ": (40.298904, -74.521011),
    "NM": (34.840515, -106.248482),
    "NY": (42.165726, -74.948051),
    "NC": (35.630066, -79.806419),
    "ND": (47.528912, -99.784012),
    "OH": (40.388783, -82.764915),
    "OK": (35.565342, -96.928917),
    "OR": (44.572021, -122.070938),
    "PA": (40.590752, -77.209755),
    "RI": (41.680893, -71.511780),
    "SC": (33.856892, -80.945007),
    "SD": (44.299782, -99.438828),
    "TN": (35.747845, -86.692345),
    "TX": (31.054487, -97.563461),
    "UT": (40.150032, -111.862434),
    "VT": (44.045876, -72.710686),
    "VA": (37.769337, -78.169968),
    "WA": (47.400902, -121.490494),
    "WV": (38.491226, -80.954453),
    "WI": (44.268543, -89.616508),
    "WY": (42.755966, -107.302490)
}


def add_google_distance_labels(state: str, cities: list[str]) -> list[str]:
    return add_distance_labels(state, cities)


def add_distance_labels(state: str, cities: list[str]) -> list[str]:
    state = state.strip().upper()
    unique_cities = sorted(set(cities))
    cache = DistanceCache()
    distances = {}
    missing_cities = []

    for city in unique_cities:
        distance_text = cache.get_distance(state, city)

        if distance_text:
            distances[city] = distance_text
        else:
            missing_cities.append(city)

    allowed_cities = _reserve_uncached_elements(len(missing_cities))
    skipped_count = len(missing_cities) - allowed_cities

    if skipped_count > 0:
        print(
            "[!] Distance limiter reached: "
            f"skipping {skipped_count} uncached city distance(s)."
        )

    origin = _state_center(state)

    for city in missing_cities[:allowed_cities]:
        destination = _geocode_city(city, state, cache)

        if not origin or not destination:
            continue

        distance_text = _straight_line_distance(origin, destination)

        if distance_text:
            distances[city] = distance_text
            cache.set_distance(state, city, distance_text)

    cache.close()

    return [
        f"{city} ({distances[city]})" if distances.get(city) else city
        for city in cities
    ]


def _geocode_city(
    city: str,
    state: str,
    cache: "DistanceCache"
) -> tuple[float, float] | None:
    coordinates = cache.get_geocode(city, state)

    if coordinates:
        return coordinates

    coordinates = _openrouteservice_geocode(city, state)

    if not coordinates:
        coordinates = _google_geocode(city, state)

    if not coordinates:
        coordinates = _nominatim_geocode(city, state)

    if coordinates:
        cache.set_geocode(city, state, coordinates)

    return coordinates


def _google_geocode(city: str, state: str) -> tuple[float, float] | None:
    api_key = os.getenv(GOOGLE_MAPS_API_KEY_ENV)

    if not api_key:
        return None

    query = f"{city}, {state}, USA"
    url = f"{GOOGLE_GEOCODE_URL}?{urlencode({'address': query, 'key': api_key})}"
    payload = _read_json(url)

    if payload.get("status") != "OK":
        return None

    results = payload.get("results", [])

    if not results:
        return None

    location = results[0].get("geometry", {}).get("location", {})
    lat = location.get("lat")
    lon = location.get("lng")

    if lat is None or lon is None:
        return None

    return float(lat), float(lon)


def _openrouteservice_geocode(city: str, state: str) -> tuple[float, float] | None:
    api_key = os.getenv(OPENROUTESERVICE_API_KEY_ENV)

    if not api_key:
        return None

    query = f"{city}, {state}, USA"
    params = {
        "api_key": api_key,
        "text": query,
        "size": 1,
        "boundary.country": "US"
    }
    url = f"{ORS_GEOCODE_URL}?{urlencode(params)}"
    payload = _read_json(url)
    features = payload.get("features", [])

    if not features:
        return None

    coordinates = features[0].get("geometry", {}).get("coordinates", [])

    if len(coordinates) < 2:
        return None

    longitude, latitude = coordinates[:2]
    return float(latitude), float(longitude)


def _nominatim_geocode(city: str, state: str) -> tuple[float, float] | None:
    _wait_for_free_provider()

    state_name = STATE_NAMES.get(state, state)
    query = f"{city}, {state_name}, USA"
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1
    }
    url = f"{NOMINATIM_URL}?{urlencode(params)}"
    payload = _read_json(url)

    if not payload:
        return None

    return float(payload[0]["lat"]), float(payload[0]["lon"])


def _straight_line_distance(
    origin: tuple[float, float],
    destination: tuple[float, float]
) -> str:
    origin_lat, origin_lon = origin
    destination_lat, destination_lon = destination
    radius_miles = 3958.8
    lat_delta = math.radians(destination_lat - origin_lat)
    lon_delta = math.radians(destination_lon - origin_lon)
    origin_lat = math.radians(origin_lat)
    destination_lat = math.radians(destination_lat)
    haversine = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(origin_lat)
        * math.cos(destination_lat)
        * math.sin(lon_delta / 2) ** 2
    )
    miles = 2 * radius_miles * math.asin(math.sqrt(haversine))
    return _format_miles(miles)


def _state_center(state: str) -> tuple[float, float] | None:
    return STATE_CENTERS.get(state)


def _reserve_uncached_elements(requested_count: int) -> int:
    global UNCACHED_ELEMENTS_USED

    if DISTANCE_MAX_UNCACHED_ELEMENTS_PER_RUN is None:
        UNCACHED_ELEMENTS_USED += requested_count
        return requested_count

    remaining = max(
        int(DISTANCE_MAX_UNCACHED_ELEMENTS_PER_RUN) - UNCACHED_ELEMENTS_USED,
        0
    )
    allowed_count = min(requested_count, remaining)
    UNCACHED_ELEMENTS_USED += allowed_count
    return allowed_count


def _wait_for_free_provider():
    global LAST_FREE_REQUEST_AT

    elapsed = time.monotonic() - LAST_FREE_REQUEST_AT

    if elapsed < DISTANCE_REQUEST_DELAY_SECONDS:
        time.sleep(DISTANCE_REQUEST_DELAY_SECONDS - elapsed)

    LAST_FREE_REQUEST_AT = time.monotonic()


def _read_json(url: str):
    request = Request(url, headers={"User-Agent": DISTANCE_USER_AGENT})

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except OSError as exc:
        print(f"[!] Distance lookup failed: {exc}")
        return {}


def _format_miles(miles: float) -> str:
    return f"{round(miles):,} mi"


class DistanceCache:
    def __init__(self):
        self.cache_path = Path(DISTANCE_CACHE_FILE)
        self.inline_legacy_cache = None
        self.cache_path.parent.mkdir(exist_ok=True)
        self._prepare_cache_file()
        self.connection = sqlite3.connect(self.cache_path)
        self._create_tables()
        self._migrate_legacy_json_cache()

    def get_distance(self, state: str, city: str) -> str | None:
        row = self.connection.execute(
            """
            SELECT distance_text
            FROM distances
            WHERE state = ? AND city = ?
            """,
            (state, city)
        ).fetchone()

        return row[0] if row else None

    def set_distance(self, state: str, city: str, distance_text: str):
        self.connection.execute(
            """
            INSERT INTO distances (state, city, distance_text)
            VALUES (?, ?, ?)
            ON CONFLICT(state, city)
            DO UPDATE SET distance_text = excluded.distance_text
            """,
            (state, city, distance_text)
        )
        self.connection.commit()

    def get_geocode(self, city: str, state: str) -> tuple[float, float] | None:
        row = self.connection.execute(
            """
            SELECT latitude, longitude
            FROM geocodes
            WHERE city = ? AND state = ?
            """,
            (city, state)
        ).fetchone()

        if not row:
            return None

        return float(row[0]), float(row[1])

    def set_geocode(self, city: str, state: str, coordinates: tuple[float, float]):
        latitude, longitude = coordinates
        self.connection.execute(
            """
            INSERT INTO geocodes (city, state, latitude, longitude)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(city, state)
            DO UPDATE SET
                latitude = excluded.latitude,
                longitude = excluded.longitude
            """,
            (city, state, latitude, longitude)
        )
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _prepare_cache_file(self):
        if not self.cache_path.exists() or _is_sqlite_file(self.cache_path):
            return

        try:
            self.inline_legacy_cache = json.loads(self.cache_path.read_text())
            backup_path = _unused_backup_path(
                self.cache_path.with_suffix(
                    f"{self.cache_path.suffix}.legacy-json"
                )
            )
        except json.JSONDecodeError:
            backup_path = _unused_backup_path(
                self.cache_path.with_suffix(
                    f"{self.cache_path.suffix}.corrupt"
                )
            )

        self.cache_path.replace(backup_path)
        print(
            "[!] Existing distance cache was not SQLite; "
            f"moved it to {backup_path}."
        )

    def _create_tables(self):
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS geocodes (
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                PRIMARY KEY (city, state)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS distances (
                state TEXT NOT NULL,
                city TEXT NOT NULL,
                distance_text TEXT NOT NULL,
                PRIMARY KEY (state, city)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def _migrate_legacy_json_cache(self):
        legacy_path = Path(DISTANCE_LEGACY_JSON_CACHE_FILE)

        if self._legacy_migration_done():
            return

        if self.inline_legacy_cache:
            self._migrate_json_cache_data(self.inline_legacy_cache)

        if legacy_path.exists():
            try:
                legacy_cache = json.loads(legacy_path.read_text())
            except json.JSONDecodeError:
                legacy_cache = None

            if legacy_cache:
                self._migrate_json_cache_data(legacy_cache)

        self._mark_legacy_migration_done()

    def _migrate_json_cache_data(self, legacy_cache: dict):
        for cache_key, coordinates in legacy_cache.get("geocodes", {}).items():
            city, state = _parse_geocode_cache_key(cache_key)

            if city and state and len(coordinates) == 2:
                self.set_geocode(city, state, tuple(coordinates))

        for cache_key, distance_text in legacy_cache.get("distances", {}).items():
            state, city = _parse_distance_cache_key(cache_key)

            if state and city:
                self.set_distance(state, city, distance_text)

    def _legacy_migration_done(self) -> bool:
        row = self.connection.execute(
            """
            SELECT value
            FROM metadata
            WHERE key = 'legacy_json_migrated'
            """
        ).fetchone()

        return bool(row and row[0] == "true")

    def _mark_legacy_migration_done(self):
        self.connection.execute(
            """
            INSERT INTO metadata (key, value)
            VALUES ('legacy_json_migrated', 'true')
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
            """
        )
        self.connection.commit()


def _parse_distance_cache_key(cache_key: str) -> tuple[str | None, str | None]:
    parts = cache_key.split("|", 1)

    if len(parts) != 2:
        return None, None

    return parts[0], parts[1]


def _parse_geocode_cache_key(cache_key: str) -> tuple[str | None, str | None]:
    parts = cache_key.rsplit(", ", 2)

    if len(parts) != 3:
        return None, None

    city, state, _country = parts
    return city, state


def _is_sqlite_file(path: Path) -> bool:
    with path.open("rb") as file:
        return file.read(16) == b"SQLite format 3\0"


def _unused_backup_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(1, 1000):
        candidate = path.with_name(f"{path.name}.{index}")

        if not candidate.exists():
            return candidate

    return path.with_name(f"{path.name}.{int(time.time())}")
