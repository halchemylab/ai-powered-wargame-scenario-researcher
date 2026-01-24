import overpy
import numpy as np
from geopy.geocoders import Nominatim
import config
import time

def get_coordinates(location_name):
    """
    Geocodes the location name to lat/lon.
    """
    geolocator = Nominatim(user_agent="wargame_researcher_v1")
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def fetch_terrain_map(location_name, grid_size=20, cell_size_meters=100):
    """
    Generates a 20x20 grid based on real OSM data.
    
    Args:
        location_name (str): City or region name.
        grid_size (int): Grid dimension (NxN).
        cell_size_meters (int): Real-world size of one grid cell.
    
    Returns:
        list[list[int]]: The terrain matrix.
    """
    coords = get_coordinates(location_name)
    if not coords:
        # Fallback to empty map if location not found
        return [[config.TerrainType.OPEN.value] * grid_size for _ in range(grid_size)]
    
    lat, lon = coords
    
    # Calculate Bounding Box
    # 1 deg lat ~ 111km. 1 deg lon ~ 111km * cos(lat).
    # Box radius in degrees
    radius_meters = (grid_size * cell_size_meters) / 2
    lat_delta = radius_meters / 111000
    lon_delta = radius_meters / (111000 * np.cos(np.radians(lat)))
    
    south = lat - lat_delta
    north = lat + lat_delta
    west = lon - lon_delta
    east = lon + lon_delta
    
    api = overpy.Overpass()
    
    # Query for features
    # optimizing query to get ways and relations (polygons)
    # [out:json];
    # (
    #   way["natural"="water"](south, west, north, east);
    #   relation["natural"="water"](south, west, north, east);
    #   way["landuse"="forest"](south, west, north, east);
    #   way["natural"="wood"](south, west, north, east);
    #   way["landuse"="residential"](south, west, north, east);
    #   way["landuse"="commercial"](south, west, north, east);
    #   way["building"](south, west, north, east);
    # );
    # (._;>;);
    # out body;
    
    query = f"""
    [out:json];
    (
      way["natural"="water"]({south},{west},{north},{east});
      relation["natural"="water"]({south},{west},{north},{east});
      way["waterway"="riverbank"]({south},{west},{north},{east});
      way["landuse"="forest"]({south},{west},{north},{east});
      way["natural"="wood"]({south},{west},{north},{east});
      way["landuse"="residential"]({south},{west},{north},{east});
      way["landuse"="industrial"]({south},{west},{north},{east});
      way["building"]({south},{west},{north},{east});
    );
    (._;>;);
    out body;
    """
    
    try:
        result = api.query(query)
    except Exception as e:
        print(f"Overpass API error: {e}")
        return [[config.TerrainType.OPEN.value] * grid_size for _ in range(grid_size)]

    # Initialize Grid (0 = Open)
    grid = np.zeros((grid_size, grid_size), dtype=int)
    
    # Helper to map lat/lon to grid x/y
    def to_grid(lat_p, lon_p):
        y = int((lat_p - south) / (north - south) * grid_size)
        x = int((lon_p - west) / (east - west) * grid_size)
        # Flip Y because grid 0,0 is usually top-left, but lat increases upwards.
        # Actually, let's keep it standard Cartesian (0,0 bottom left) for calculation 
        # then flip at end if needed. Or just match typical array indexing where 0 is top.
        # Let's use 0 = Top (North) to match the UI map usually.
        # So Lat North = Index 0. Lat South = Index N.
        y_inv = grid_size - 1 - y
        return x, y_inv

    # Rasterize Ways
    for way in result.ways:
        tags = way.tags
        t_type = config.TerrainType.OPEN.value
        
        if "water" in tags.get("natural", "") or "riverbank" in tags.get("waterway", ""):
            t_type = config.TerrainType.WATER.value
        elif "forest" in tags.get("landuse", "") or "wood" in tags.get("natural", ""):
            t_type = config.TerrainType.FOREST.value
        elif "residential" in tags.get("landuse", "") or "industrial" in tags.get("landuse", "") or "building" in tags:
            t_type = config.TerrainType.URBAN.value
        
        # Simple point sampling for the way nodes
        # A better way would be polygon filling, but for a 20x20 grid, 
        # sampling nodes + drawing lines is 'okay' approximation.
        nodes = way.nodes
        for i in range(len(nodes)):
            n1 = nodes[i]
            x1, y1 = to_grid(float(n1.lat), float(n1.lon))
            
            if 0 <= x1 < grid_size and 0 <= y1 < grid_size:
                grid[y1][x1] = t_type
            
            # Interpolate to fill gaps (Bresenham-ish)
            if i > 0:
                n0 = nodes[i-1]
                x0, y0 = to_grid(float(n0.lat), float(n0.lon))
                
                # Simple linear interpolation
                dist = max(abs(x1-x0), abs(y1-y0))
                if dist > 0:
                    for step in range(dist):
                        t = step / dist
                        xi = int(x0 + (x1 - x0) * t)
                        yi = int(y0 + (y1 - y0) * t)
                        if 0 <= xi < grid_size and 0 <= yi < grid_size:
                             # Precedence: Water > Urban > Forest > Open
                             # Or whatever layer logic.
                             # If we already have something set, maybe don't overwrite if lower priority?
                             # Let's just overwrite for now.
                             grid[yi][xi] = t_type

    return grid.tolist()
