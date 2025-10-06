from mcp.server.fastmcp import FastMCP
import requests
import time
from typing import Optional, List, Dict, Any
from urllib.parse import quote

# Initialize FastMCP server
mcp = FastMCP("openstreetmap")

# Base URLs for OpenStreetMap services
NOMINATIM_URL = "https://nominatim.openstreetmap.org"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSRM_URL = "http://router.project-osrm.org"

# User agent (required by Nominatim)
HEADERS = {
    "User-Agent": "MCP-OpenStreetMap-Server/1.0"
}

def rate_limit():
    """Respect Nominatim's rate limit of 1 request per second"""
    time.sleep(1)


@mcp.tool()
def maps_geocode(address: str) -> Dict[str, Any]:
    """
    Convert an address to geographic coordinates using OpenStreetMap.
    
    Args:
        address: The address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA")
    
    Returns:
        Dictionary containing location (lat/lng), formatted_address, and place_id
    """
    try:
        rate_limit()
        url = f"{NOMINATIM_URL}/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        
        if not result:
            return {"error": "No results found for the given address"}
        
        place = result[0]
        return {
            "location": {
                "lat": float(place["lat"]),
                "lng": float(place["lon"])
            },
            "formatted_address": place.get("display_name"),
            "place_id": place.get("place_id")
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def maps_reverse_geocode(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Convert coordinates to a human-readable address.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Dictionary containing formatted_address, place_id, and address_components
    """
    try:
        rate_limit()
        url = f"{NOMINATIM_URL}/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json"
        }
        
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            return {"error": "No results found for the given coordinates"}
        
        address = result.get("address", {})
        return {
            "formatted_address": result.get("display_name"),
            "place_id": result.get("place_id"),
            "address_components": address
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def maps_search_places(
    query: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Search for places using a text query.
    
    Args:
        query: The search query (e.g., "pizza", "Eiffel Tower")
        latitude: Optional latitude for location-biased search
        longitude: Optional longitude for location-biased search
        radius: Optional search radius in meters (max 50000)
    
    Returns:
        List of places with names, addresses, and locations
    """
    try:
        rate_limit()
        url = f"{NOMINATIM_URL}/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 10
        }
        
        if latitude is not None and longitude is not None:
            params["lat"] = latitude
            params["lon"] = longitude
        
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        results = response.json()
        
        places = []
        for place in results:
            places.append({
                "name": place.get("name", place.get("display_name").split(",")[0]),
                "address": place.get("display_name"),
                "location": {
                    "lat": float(place["lat"]),
                    "lng": float(place["lon"])
                },
                "place_id": place.get("place_id"),
                "type": place.get("type"),
                "importance": place.get("importance")
            })
        
        return places
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def maps_place_details(place_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific place.
    
    Args:
        place_id: The OpenStreetMap place ID
    
    Returns:
        Detailed place information including name, address, and available metadata
    """
    try:
        rate_limit()
        url = f"{NOMINATIM_URL}/lookup"
        params = {
            "osm_ids": f"N{place_id}",
            "format": "json",
            "addressdetails": 1,
            "extratags": 1
        }
        
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        
        if not result:
            return {"error": "Place not found"}
        
        place = result[0]
        extratags = place.get("extratags", {})
        
        return {
            "name": place.get("name", place.get("display_name").split(",")[0]),
            "formatted_address": place.get("display_name"),
            "phone": extratags.get("phone", extratags.get("contact:phone")),
            "website": extratags.get("website", extratags.get("contact:website")),
            "location": {
                "lat": float(place["lat"]),
                "lng": float(place["lon"])
            },
            "type": place.get("type"),
            "category": place.get("category"),
            "opening_hours": extratags.get("opening_hours"),
            "address_components": place.get("address", {})
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def maps_distance_matrix(
    origins: List[str],
    destinations: List[str],
    mode: str = "driving"
) -> Dict[str, Any]:
    """
    Calculate distances and travel times between multiple origins and destinations.
    
    Args:
        origins: List of origin addresses
        destinations: List of destination addresses
        mode: Travel mode - "driving", "walking", "bicycling" (transit not supported)
    
    Returns:
        Matrix of distances and durations between all origin-destination pairs
    """
    try:
        # First geocode all origins and destinations
        origin_coords = []
        for origin in origins:
            rate_limit()
            geocode_result = maps_geocode(origin)
            if "error" not in geocode_result:
                origin_coords.append(geocode_result["location"])
        
        dest_coords = []
        for dest in destinations:
            rate_limit()
            geocode_result = maps_geocode(dest)
            if "error" not in geocode_result:
                dest_coords.append(geocode_result["location"])
        
        # Map mode to OSRM profile
        mode_map = {
            "driving": "car",
            "walking": "foot",
            "bicycling": "bike"
        }
        profile = mode_map.get(mode, "car")
        
        rows = []
        for origin in origin_coords:
            elements = []
            for dest in dest_coords:
                try:
                    url = f"{OSRM_URL}/route/v1/{profile}/{origin['lng']},{origin['lat']};{dest['lng']},{dest['lat']}"
                    params = {"overview": "false"}
                    
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get("code") == "Ok" and result.get("routes"):
                        route = result["routes"][0]
                        elements.append({
                            "distance": {
                                "text": f"{route['distance']/1000:.1f} km",
                                "value": route["distance"]
                            },
                            "duration": {
                                "text": f"{route['duration']/60:.0f} mins",
                                "value": route["duration"]
                            },
                            "status": "OK"
                        })
                    else:
                        elements.append({"status": "NOT_FOUND"})
                except:
                    elements.append({"status": "ERROR"})
            
            rows.append({"elements": elements})
        
        return {
            "origin_addresses": origins,
            "destination_addresses": destinations,
            "rows": rows
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def maps_elevation(locations: List[Dict[str, float]]) -> List[Dict[str, Any]]:
    """
    Get elevation data for one or more locations using Open-Elevation API.
    
    Args:
        locations: List of location dictionaries with 'latitude' and 'longitude' keys
    
    Returns:
        List of elevation data for each location
    """
    try:
        url = "https://api.open-elevation.com/api/v1/lookup"
        
        locations_param = [
            {"latitude": loc["latitude"], "longitude": loc["longitude"]}
            for loc in locations
        ]
        
        response = requests.post(url, json={"locations": locations_param})
        response.raise_for_status()
        result = response.json()
        
        return [
            {
                "elevation": point["elevation"],
                "location": {
                    "lat": point["latitude"],
                    "lng": point["longitude"]
                }
            }
            for point in result.get("results", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def maps_directions(
    origin: str,
    destination: str,
    mode: str = "driving"
) -> Dict[str, Any]:
    """
    Get directions between two points.
    
    Args:
        origin: Starting address or coordinates
        destination: Ending address or coordinates
        mode: Travel mode - "driving", "walking", "bicycling" (transit not supported)
    
    Returns:
        Detailed route information with steps, distance, and duration
    """
    try:
        # Geocode origin and destination
        rate_limit()
        origin_geo = maps_geocode(origin)
        if "error" in origin_geo:
            return {"error": f"Could not geocode origin: {origin}"}
        
        rate_limit()
        dest_geo = maps_geocode(destination)
        if "error" in dest_geo:
            return {"error": f"Could not geocode destination: {destination}"}
        
        # Map mode to OSRM profile
        mode_map = {
            "driving": "car",
            "walking": "foot",
            "bicycling": "bike"
        }
        profile = mode_map.get(mode, "car")
        
        origin_loc = origin_geo["location"]
        dest_loc = dest_geo["location"]
        
        url = f"{OSRM_URL}/route/v1/{profile}/{origin_loc['lng']},{origin_loc['lat']};{dest_loc['lng']},{dest_loc['lat']}"
        params = {
            "overview": "full",
            "steps": "true",
            "geometries": "geojson"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != "Ok" or not result.get("routes"):
            return {"error": "No route found"}
        
        route = result["routes"][0]
        leg = route["legs"][0]
        
        steps = []
        for step in leg.get("steps", []):
            steps.append({
                "instruction": step.get("name", "Continue"),
                "distance": {
                    "text": f"{step['distance']/1000:.1f} km",
                    "value": step["distance"]
                },
                "duration": {
                    "text": f"{step['duration']/60:.0f} mins",
                    "value": step["duration"]
                },
                "travel_mode": mode.upper()
            })
        
        return {
            "summary": f"Route via {profile}",
            "distance": {
                "text": f"{route['distance']/1000:.1f} km",
                "value": route["distance"]
            },
            "duration": {
                "text": f"{route['duration']/60:.0f} mins",
                "value": route["duration"]
            },
            "start_address": origin_geo["formatted_address"],
            "end_address": dest_geo["formatted_address"],
            "start_location": origin_loc,
            "end_location": dest_loc,
            "steps": steps
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")