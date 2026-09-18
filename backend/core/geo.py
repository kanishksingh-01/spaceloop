"""
SpaceLoop Geospatial Helpers
Haversine distance calculation and location resolution for spaces and geofenced door passes.
"""
import math

KNOWN_HUBS = {
    "hauz khas": (28.5450, 77.1926),
    "iit delhi": (28.5450, 77.1926),
    "delhi": (28.5450, 77.1926),
    "new delhi": (28.5450, 77.1926),
    "north campus": (28.6900, 77.2100),
    "delhi university": (28.6900, 77.2100),
    "connaught place": (28.6315, 77.2167),
    "safdarjung": (28.5672, 77.1950),
    "cyber city": (28.4900, 77.0900),
    "noida": (28.6270, 77.3725),
    "sector 62": (28.6270, 77.3725),
    "koramangala": (12.9352, 77.6245),
    "bangalore": (12.9352, 77.6245),
    "bengaluru": (12.9352, 77.6245),
    "indiranagar": (12.9784, 77.6408),
    "electronic city": (12.8452, 77.6602),
    "shivajinagar": (18.5204, 73.8567),
    "fc road": (18.5204, 73.8567),
    "pune": (18.5204, 73.8567),
    "wagholi": (18.5793, 73.9822),
    "viman nagar": (18.5679, 73.9143),
    "kothrud": (18.5074, 73.8077),
    "aundh": (18.5601, 73.8031),
    "baner": (18.5590, 73.7868),
    "downtown": (18.5590, 73.7868),
    "bandra": (19.0596, 72.8295),
    "powai": (19.1334, 72.9133),
    "mumbai": (19.1334, 72.9133),
    "iit bombay": (19.1334, 72.9133)
}


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between two GPS coordinates in meters using the Haversine formula."""
    try:
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except Exception:
        return 0.0


def resolve_location_coordinates(loc_name="", lat=None, lng=None):
    """
    Resolves human location name or GPS coordinates into (lat, lng, display_name).
    """
    if lat is not None and lng is not None:
        try:
            fl_lat = float(lat)
            fl_lng = float(lng)
            if -90.0 <= fl_lat <= 90.0 and -180.0 <= fl_lng <= 180.0:
                name = loc_name or "Current GPS Location"
                return fl_lat, fl_lng, name
        except (ValueError, TypeError):
            pass

    if loc_name:
        clean = loc_name.strip()
        if "," in clean:
            parts = clean.split(",")
            if len(parts) == 2:
                try:
                    fl_lat = float(parts[0].strip())
                    fl_lng = float(parts[1].strip())
                    if -90.0 <= fl_lat <= 90.0 and -180.0 <= fl_lng <= 180.0:
                        return fl_lat, fl_lng, f"{round(fl_lat, 3)}, {round(fl_lng, 3)}"
                except (ValueError, TypeError):
                    pass

        clean_lower = clean.lower()
        # Sort hubs by key length descending so specific hubs (e.g. 'hauz khas') match before 'delhi'
        sorted_hubs = sorted(KNOWN_HUBS.items(), key=lambda item: len(item[0]), reverse=True)
        for hub_key, coords in sorted_hubs:
            if hub_key in clean_lower or clean_lower in hub_key:
                return coords[0], coords[1], hub_key.title()

    return None, None, ""
