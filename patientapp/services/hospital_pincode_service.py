"""
patientapp/services/hospital_pincode_service.py
================================================
Service to look up and recommend nearest participating hospitals by Pincode.

Provides:
- Exact 6-digit pincode matching
- Regional prefix matching (same postal delivery zone)
- Hospital serialization with full address, contact details, and distance cues.
"""

import re
from typing import Dict, Any, List
from hospitalapp.models import Hospitaltbl


def find_nearest_hospitals_by_pincode(pincode: str, limit: int = 6) -> Dict[str, Any]:
    """
    Finds and ranks hospitals by proximity to the provided Indian 6-digit Pincode.

    Ranking Order:
    1. Exact Pincode match (matches the entire 6 digits)
    2. Sub-district / Zone match (matches first 4 digits, e.g. 3900xx)
    3. State / District match (matches first 3 digits, e.g. 390xxx)
    4. General participating hospitals fallback
    """
    pincode_str = str(pincode or "").strip()
    
    # Validation: Must be 6 digits
    clean_pincode = re.sub(r"\D", "", pincode_str)
    if not clean_pincode or len(clean_pincode) != 6:
        return {
            "success": False,
            "pincode": pincode_str,
            "total_found": 0,
            "hospitals": [],
            "message": "Please enter a valid 6-digit Pincode (e.g. 390001).",
        }

    all_hospitals = Hospitaltbl.objects.select_related("cityId", "areaId").all()

    exact_matches: List[Dict[str, Any]] = []
    zone_matches: List[Dict[str, Any]] = []
    district_matches: List[Dict[str, Any]] = []
    seen_ids = set()

    prefix_4 = clean_pincode[:4]
    prefix_3 = clean_pincode[:3]

    for h in all_hospitals:
        h_pin = str(h.pincode or "").strip()
        
        # If pincode not stored in field, attempt regex extraction from address
        if not h_pin:
            match = re.search(r"\b39\d{4}\b", h.address)
            if match:
                h_pin = match.group(0)

        serialized = _serialize_hospital(h, h_pin)

        if h_pin == clean_pincode:
            serialized["match_type"] = "EXACT_PINCODE"
            serialized["is_exact_match"] = True
            serialized["badge"] = f"Exact Pincode Match ({clean_pincode})"
            exact_matches.append(serialized)
            seen_ids.add(h.id)
        elif h_pin.startswith(prefix_4):
            serialized["match_type"] = "ZONE_MATCH"
            serialized["is_exact_match"] = False
            serialized["badge"] = f"Nearby Area ({h_pin})"
            zone_matches.append(serialized)
        elif h_pin.startswith(prefix_3):
            serialized["match_type"] = "DISTRICT_MATCH"
            serialized["is_exact_match"] = False
            serialized["badge"] = f"Regional ({h_pin})"
            district_matches.append(serialized)

    # Compile result list with priority ranking
    results: List[Dict[str, Any]] = []
    results.extend(exact_matches)

    for item in zone_matches:
        if item["id"] not in seen_ids and len(results) < limit:
            results.append(item)
            seen_ids.add(item["id"])

    for item in district_matches:
        if item["id"] not in seen_ids and len(results) < limit:
            results.append(item)
            seen_ids.add(item["id"])

    # If still fewer than limit, include general active hospitals
    if len(results) < limit:
        for h in all_hospitals:
            if h.id not in seen_ids and len(results) < limit:
                ser = _serialize_hospital(h, str(h.pincode or "390001"))
                ser["match_type"] = "GENERAL_FALLBACK"
                ser["is_exact_match"] = False
                ser["badge"] = "Participating Hospital"
                results.append(ser)
                seen_ids.add(h.id)

    total_found = len(results)
    exact_count = len(exact_matches)

    if exact_count > 0:
        msg = f"Found {exact_count} hospital(s) directly in pincode {clean_pincode}."
    elif total_found > 0:
        msg = f"Showing {total_found} nearest participating hospitals in your region (Pincode {clean_pincode})."
    else:
        msg = f"No participating hospitals found near Pincode {clean_pincode}."

    return {
        "success": True,
        "pincode": clean_pincode,
        "total_found": total_found,
        "exact_count": exact_count,
        "hospitals": results[:limit],
        "message": msg,
    }


def _serialize_hospital(h: Hospitaltbl, pincode: str) -> Dict[str, Any]:
    """Serialize hospital object into a clean dictionary."""
    return {
        "id": h.id,
        "title": h.title,
        "dcrname": h.dcrname or "",
        "address": h.address,
        "pincode": pincode,
        "cityName": h.cityId.cityName if h.cityId else "",
        "areaName": h.areaId.areaName if h.areaId else "",
        "contactNo": str(h.contactNo) if h.contactNo else "",
        "opening_time": str(h.opening_time) if h.opening_time else "09:00 AM",
        "closing_time": str(h.closing_time) if h.closing_time else "05:00 PM",
        "img_url": h.HospitalImageUrl() if hasattr(h, "HospitalImageUrl") else "/static/profileimg/noimg.png",
    }
