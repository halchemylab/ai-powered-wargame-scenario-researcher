import math
import config
from engine import models

def validate_scenario(scenario: models.WargameScenario):
    """
    Runs physics and logic checks on a scenario. 
    Populates the validation_errors field of each frame.
    """
    
    # Track unit positions from previous frame
    # Dict[unit_id, Unit]
    prev_units = {}
    
    # Get map dimensions
    map_height = len(scenario.terrain_map)
    map_width = len(scenario.terrain_map[0]) if map_height > 0 else 0
    
    for frame_idx, frame in enumerate(scenario.frames):
        # Reset errors for re-validation
        frame.validation_errors = []
        current_units = {u.unit_id: u for u in frame.unit_positions}
        
        # 1. Terrain Collision (Water) & Bounds
        for unit in frame.unit_positions:
            # Check bounds first
            if not (0 <= unit.x < map_width and 0 <= unit.y < map_height):
                 frame.validation_errors.append(f"Unit {unit.unit_id} out of bounds ({unit.x}, {unit.y})")
                 continue
                 
            try:
                terrain = scenario.terrain_map[unit.y][unit.x]
                if terrain == config.TerrainType.WATER.value:
                    # We could check for 'amphibious' type, but for now assuming all are blocked
                    frame.validation_errors.append(f"Unit {unit.unit_id} is in Water at ({unit.x}, {unit.y})")
            except IndexError:
                pass # Already caught by bounds check

        # 2. Movement Logic (vs Previous Frame)
        if frame_idx > 0:
            for unit_id, unit in current_units.items():
                if unit_id in prev_units:
                    prev = prev_units[unit_id]
                    dist = math.sqrt((unit.x - prev.x)**2 + (unit.y - prev.y)**2)
                    
                    # Max speed threshold (e.g., 2.9 to allow diagonal 2-step which is 2.82)
                    # Let's be generous and say 3.0 to account for minor AI glitches
                    if dist > 3.0:
                         frame.validation_errors.append(f"Unit {unit.unit_id} moved too fast ({dist:.2f} tiles)")
        
        # Update prev_units for next iteration
        prev_units = current_units