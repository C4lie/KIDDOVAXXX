import math
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

# Fallback coordinates dictionary for cities/areas when offline or rate-limited
FALLBACK_COORDINATES = {
    # Cities
    "surat": (21.1702, 72.8311),
    "vadodara": (22.3072, 73.1812),
    "ahmedabad": (23.0225, 72.5714),
    "mumbai": (19.0760, 72.8777),
    "rajkot": (22.3039, 70.8022),
    
    # Areas in Surat
    "adajan": (21.1959, 72.7933),
    "varachha": (21.2139, 72.8624),
    "vesu": (21.1418, 72.7709),
    "katargam": (21.2266, 72.8258),
    "rander": (21.2185, 72.7981),
    
    # Areas in Vadodara
    "alkapuri": (22.3106, 73.1726),
    "gotri": (22.3218, 73.1419),
    "sayajigunj": (22.3090, 73.1895),
}

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points in kilometers using the Haversine formula.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
        
    R = 6371.0  # Earth radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
         
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return round(distance, 2)


def geocode_location(address_or_area: str, city_name: str = None) -> tuple:
    """
    Geocodes a location string using OpenStreetMap Nominatim.
    Falls back to local coordinate lookup dictionary if network fails or yields no result.
    Returns (latitude, longitude) tuple or (None, None).
    """
    query_parts = []
    if address_or_area:
        query_parts.append(address_or_area)
    if city_name:
        query_parts.append(city_name)
    query_parts.append("India")

    query_str = ", ".join(query_parts)

    # 1. Try Nominatim API
    try:
        encoded_query = urllib.parse.quote(query_str)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'KiddoVax-App/1.0 (contact@kiddovax.org)'}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    return (lat, lon)
    except Exception as e:
        logger.warning(f"Nominatim geocoding failed for '{query_str}': {e}")

    # 2. Local fallback dictionary lookup
    lookup_key = (address_or_area or '').strip().lower()
    if lookup_key in FALLBACK_COORDINATES:
        return FALLBACK_COORDINATES[lookup_key]

    city_key = (city_name or '').strip().lower()
    if city_key in FALLBACK_COORDINATES:
        return FALLBACK_COORDINATES[city_key]

    return (None, None)


def sort_hospitals_by_recommendation(hospitals_qs, user_lat=None, user_lng=None, vaccine_name=None, child_id=None):
    """
    Filters and sorts hospitals by:
    1. Vaccine availability (if vaccine_name specified, hospital must have matching stock/catalogue).
    2. Proximity (distance ascending if user_lat and user_lng are provided).
    Returns list of dicts: [{hospital, distance_km, is_nearest, vaccine_available}, ...]
    """
    results = []
    
    for hosp in hospitals_qs:
        # Check coordinates (fallback to city/area lookup if hospital has no coordinates)
        hosp_lat = hosp.latitude
        hosp_lng = hosp.longitude
        
        if hosp_lat is None or hosp_lng is None:
            area_name = hosp.areaId.areaName if hosp.areaId else None
            city_name = hosp.cityId.cityName if hosp.cityId else None
            hosp_lat, hosp_lng = geocode_location(area_name, city_name)
            
            # Save resolved coordinates back to hospital if found
            if hosp_lat and hosp_lng and (hosp.latitude is None or hosp.longitude is None):
                hosp.latitude = hosp_lat
                hosp.longitude = hosp_lng
                hosp.save(update_fields=['latitude', 'longitude'])

        # Calculate distance
        dist = None
        if user_lat is not None and user_lng is not None and hosp_lat is not None and hosp_lng is not None:
            dist = calculate_haversine_distance(user_lat, user_lng, hosp_lat, hosp_lng)

        # Check vaccine availability
        vaccine_available = True
        vaccine_obj = None
        if vaccine_name:
            matching_vaccine = hosp.vaccinetbl_set.filter(vaccineName__icontains=vaccine_name).first()
            if not matching_vaccine:
                vaccine_available = False
            else:
                vaccine_obj = matching_vaccine

        results.append({
            'hospital': hosp,
            'distance_km': dist,
            'vaccine_available': vaccine_available,
            'vaccine': vaccine_obj,
            'is_nearest': False
        })

    # Sort logic:
    # 1. Eligible hospitals first (vaccine_available=True)
    # 2. Distance ascending (if distance is not None), else by ID
    def sort_key(item):
        has_vaccine = 0 if item['vaccine_available'] else 1
        distance = item['distance_km'] if item['distance_km'] is not None else 999999.0
        return (has_vaccine, distance, item['hospital'].id)

    results.sort(key=sort_key)

    # Mark the first eligible hospital with distance as nearest
    eligible = [r for r in results if r['vaccine_available']]
    if eligible and eligible[0]['distance_km'] is not None:
        eligible[0]['is_nearest'] = True
    elif results and results[0]['distance_km'] is not None:
        results[0]['is_nearest'] = True

    return results
