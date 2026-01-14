import pandas as pd
import config

def calculate_force_correlation(scenario):
    """
    Calculates the number of units for each side per frame.
    
    Args:
        scenario (WargameScenario): The scenario object.
        
    Returns:
        pd.DataFrame: DataFrame with columns ['Frame', 'Blue Force', 'Red Force'].
    """
    data = []
    
    for i, frame in enumerate(scenario.frames):
        blue_count = 0
        red_count = 0
        
        if frame.unit_positions:
            for unit in frame.unit_positions:
                if unit.side == config.UnitSide.BLUE:
                    blue_count += 1
                else:
                    red_count += 1
        
        data.append({
            'Frame': i + 1,
            'Blue Force': blue_count,
            'Red Force': red_count
        })
        
    return pd.DataFrame(data).set_index('Frame')

def calculate_heatmap(scenario):
    """
    Calculates a heat map of unit presence over the entire scenario.
    
    Args:
        scenario (WargameScenario): The scenario object.
        
    Returns:
        list[list[int]]: A 2D grid of the same dimensions as the terrain map, 
                         where values represent the count of units that have occupied that cell.
    """
    if not scenario.terrain_map:
        return []
        
    height = len(scenario.terrain_map)
    width = len(scenario.terrain_map[0]) if height > 0 else 0
    
    # Initialize zero grid
    heatmap = [[0 for _ in range(width)] for _ in range(height)]
    
    for frame in scenario.frames:
        if frame.unit_positions:
            for unit in frame.unit_positions:
                # Ensure unit is within bounds (just in case)
                if 0 <= unit.y < height and 0 <= unit.x < width:
                    heatmap[unit.y][unit.x] += 1
                    
    return heatmap
