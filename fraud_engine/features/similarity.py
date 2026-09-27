"""
SpaceLoop Feature Extraction Layer - Similarity & Mathematical Utilities
NumPy-powered vector math, modified Z-scores, Haversine geo-distance, and deterministic NLP text similarity.
"""
import re
from typing import List, Optional, Set, Tuple
import numpy as np

# Canonical disposable email domains
DISPOSABLE_DOMAINS = frozenset([
    "mailinator.com", "guerrillamail.com", "tempmail.com", "10minutemail.com",
    "throwawaymail.com", "trashmail.com", "sharklasers.com", "yopmail.com",
    "dispostable.com", "getairmail.com", "temp-mail.org", "fakeinbox.com",
    "inboxkitten.com", "burnermail.io", "mytemp.email"
])

# Canonical coordinates for major Indian metro hubs (lat, lng, max_radius_km)
INDIA_METRO_COORDS = {
    "delhi": (28.6139, 77.2090, 80.0),
    "new delhi": (28.6139, 77.2090, 80.0),
    "noida": (28.5355, 77.3910, 50.0),
    "gurgaon": (28.4595, 77.0266, 60.0),
    "gurugram": (28.4595, 77.0266, 60.0),
    "bangalore": (12.9716, 77.5946, 80.0),
    "bengaluru": (12.9716, 77.5946, 80.0),
    "mumbai": (19.0760, 72.8777, 80.0),
    "pune": (18.5204, 73.8567, 70.0),
    "hyderabad": (17.3850, 78.4867, 80.0),
    "chennai": (13.0827, 80.2707, 70.0),
    "kolkata": (22.5726, 88.3639, 70.0),
    "ahmedabad": (23.0225, 72.5714, 60.0),
}


def is_disposable_email(email: str) -> bool:
    """Checks if an email domain matches known disposable / burner email domains."""
    if not email or "@" not in email:
        return False
    domain = email.strip().lower().split("@")[-1]
    return domain in DISPOSABLE_DOMAINS


def compute_haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Computes great-circle distance between two GPS coordinates using NumPy."""
    try:
        r = 6371.0  # Earth radius in kilometers
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lng2 - lng1)

        a = np.sin(dphi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0)**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        return float(r * c)
    except Exception:
        return 0.0


def tokenize(text: str) -> Set[str]:
    """Tokenizes text into normalized lowercase alphanumeric words."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
    return set(words)


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates word-level Jaccard set similarity between two texts."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    return float(intersection / union) if union > 0 else 0.0


def calculate_ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """Calculates character n-gram Dice similarity between two strings."""
    if not text1 or not text2:
        return 0.0
    s1 = re.sub(r"\s+", " ", text1.strip().lower())
    s2 = re.sub(r"\s+", " ", text2.strip().lower())
    if s1 == s2:
        return 1.0
    if len(s1) < n or len(s2) < n:
        return 1.0 if s1 == s2 else 0.0

    ngrams1 = [s1[i:i+n] for i in range(len(s1) - n + 1)]
    ngrams2 = [s2[i:i+n] for i in range(len(s2) - n + 1)]

    set1, set2 = set(ngrams1), set(ngrams2)
    intersection = len(set1.intersection(set2))
    total = len(set1) + len(set2)
    return float((2.0 * intersection) / total) if total > 0 else 0.0


def calculate_modified_zscore(value: float, sample_values: List[float]) -> float:
    """
    Computes Boris Iglewicz & David Hoaglin Modified Z-Score:
    ModZ = 0.6745 * (x - median) / MAD
    Resistant to outliers and non-normal distributions.
    """
    if not sample_values or len(sample_values) < 3 or value is None:
        return 0.0
    arr = np.array(sample_values, dtype=np.float64)
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    if mad == 0.0:
        # Fallback to standard deviation if MAD is zero
        std = np.std(arr)
        return float(round((value - med) / std, 2)) if std > 0 else 0.0
    mod_z = 0.6745 * (value - med) / mad
    return float(round(mod_z, 2))


def check_conflicting_city_coordinates(city: str, lat: float, lng: float) -> Tuple[bool, float]:
    """
    Returns (is_conflicting, distance_km) if coordinates disagree with claimed Indian city.
    """
    if not city or lat is None or lng is None or (lat == 0.0 and lng == 0.0):
        return False, 0.0
    normalized_city = city.strip().lower()
    if normalized_city in INDIA_METRO_COORDS:
        target_lat, target_lng, max_radius = INDIA_METRO_COORDS[normalized_city]
        dist_km = compute_haversine_distance_km(lat, lng, target_lat, target_lng)
        if dist_km > max_radius:
            return True, float(round(dist_km, 1))
    return False, 0.0
