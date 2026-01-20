import pytest
from engine.ai_handler import WargameScenario, Frame, Unit
from engine import validator
import config

def test_validation_movement_speed():
    # Setup a scenario with two frames where a unit moves too fast
    unit1 = Unit(unit_id="U1", side=config.UnitSide.BLUE, type="Tank", x=0, y=0, health=100, range=1, status="Active")
    unit1_moved = Unit(unit_id="U1", side=config.UnitSide.BLUE, type="Tank", x=10, y=10, health=100, range=1, status="Active") # Moved way too far
    
    frame1 = Frame(frame_description="Start", unit_positions=[unit1], combat_log=[])
    frame2 = Frame(frame_description="End", unit_positions=[unit1_moved], combat_log=[])
    
    scenario = WargameScenario(
        terrain_map=[[0]*20 for _ in range(20)],
        frames=[frame1, frame2]
    )
    
    validator.validate_scenario(scenario)
    
    assert len(scenario.frames[1].validation_errors) > 0
    assert "moved too fast" in scenario.frames[1].validation_errors[0]

def test_validation_water_collision():
    # Setup map with water at (1,1)
    terrain = [[0]*20 for _ in range(20)]
    terrain[1][1] = config.TerrainType.WATER.value
    
    unit1 = Unit(unit_id="U1", side=config.UnitSide.RED, type="Infantry", x=1, y=1, health=100, range=1, status="Active")
    
    frame1 = Frame(frame_description="Start", unit_positions=[unit1], combat_log=[])
    
    scenario = WargameScenario(
        terrain_map=terrain,
        frames=[frame1]
    )
    
    validator.validate_scenario(scenario)
    
    assert len(scenario.frames[0].validation_errors) > 0
    assert "is in Water" in scenario.frames[0].validation_errors[0]
