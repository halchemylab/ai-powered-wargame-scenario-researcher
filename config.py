from enum import IntEnum, Enum

# --- Enums ---

class TerrainType(IntEnum):
    OPEN = 0
    WATER = 1
    URBAN = 2
    FOREST = 3

class UnitSide(str, Enum):
    BLUE = "Blue"
    RED = "Red"

# --- Visual Settings (Map Renderer) ---

# Color constants
COLOR_OPEN = '#d2b48c'   # Tan
COLOR_WATER = '#4682b4'  # SteelBlue
COLOR_URBAN = '#696969'  # DimGray
COLOR_FOREST = '#228b22' # ForestGreen

# Map integer to color
TERRAIN_COLORSCALE = [
    [0.0, COLOR_OPEN],   [0.25, COLOR_OPEN],
    [0.25, COLOR_WATER], [0.5, COLOR_WATER],
    [0.5, COLOR_URBAN],  [0.75, COLOR_URBAN],
    [0.75, COLOR_FOREST], [1.0, COLOR_FOREST]
]

# Unit Icons Mapping
UNIT_ICONS = {
    "infantry": "💂",
    "tank": "🛡️",
    "armor": "🛡️",
    "artillery": "🎯",
    "recon": "👁️",
    "scout": "👁️",
    "hq": "🚩",
    "command": "🚩",
    "mechanized": "🚜",
    "default": "⏺️"
}

# --- AI Configuration (AI Handler) ---

SYSTEM_PROMPT = f"""
You are an expert military simulation engine. Your task is to generate realistic tactical wargame scenarios based on a user's research topic.

**Output Format:**
You must output a valid JSON object matching the provided schema.

**Constraints & Rules:**
1.  **Grid:** The map is a 20x20 grid. Coordinates are (0,0) to (19,19).
2.  **Terrain:** Generate a tactical terrain map (20x20 matrix) using integers: 
    *   {TerrainType.OPEN.value}: Open Ground (plains, desert)
    *   {TerrainType.WATER.value}: Water (rivers, lakes)
    *   {TerrainType.URBAN.value}: Urban (buildings, towns)
    *   {TerrainType.FOREST.value}: Forest (woods, jungle)
    Make the terrain tactically interesting (chokepoints, cover).
3.  **Sides:** Use '{UnitSide.BLUE.value}' (Side A) and '{UnitSide.RED.value}' (Side B).
4.  **Movement Physics (Spatial Consistency):** 
    *   Units CANNOT teleport.
    *   Between consecutive frames, a unit can move a MAXIMUM of 2 squares (Euclidean distance approx, or 2 steps).
    *   Units cannot move into Deep Water ({TerrainType.WATER.value}) unless they are amphibious (context dependent, generally avoid).
5.  **Consistency:** Unit IDs must remain constant across frames. If a unit is destroyed, remove it from the list in subsequent frames.
6.  **Narrative:** The `frame_description` should briefly explain the maneuver (e.g., "Red forces flank left while Blue holds the urban center.").

**Task:**
Generate a scenario with 5-10 frames based on the user's input context.
"""
