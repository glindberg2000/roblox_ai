import math
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

def calculate_distance(pos: Tuple[float, float, float], loc_coords: Tuple[float, float, float]) -> float:
    """Calculate 3D distance between two points"""
    return math.sqrt(
        (pos[0] - loc_coords[0])**2 + 
        (pos[1] - loc_coords[1])**2 + 
        (pos[2] - loc_coords[2])**2
    )

def find_nearest_location(x: float, y: float, z: float, location_cache: Dict) -> str:
    """Find nearest location from cache"""
    if not location_cache:
        return "Unknown Area"
        
    min_distance = float('inf')
    nearest = "Unknown Area"
    
    for slug, loc_data in location_cache.items():
        loc_coords = loc_data["coordinates"]
        distance = calculate_distance((x, y, z), loc_coords)
        
        if distance < min_distance:
            min_distance = distance
            nearest = loc_data["name"]
    
    return nearest if min_distance <= 15 else "Unknown Area" 