import pytest
from engine.ai_handler import WargameScenario, Frame, Unit

@pytest.fixture
def sample_scenario():
    """Returns a basic WargameScenario object for testing."""
    return WargameScenario(
        terrain_map=[[0 for _ in range(20)] for _ in range(20)],
        frames=[
            Frame(
                frame_description="Start",
                unit_positions=[
                    Unit(unit_id="A1", side="Blue", type="Infantry", x=0, y=0),
                    Unit(unit_id="B1", side="Red", type="Tank", x=19, y=19)
                ]
            ),
            Frame(
                frame_description="Move",
                unit_positions=[
                    Unit(unit_id="A1", side="Blue", type="Infantry", x=0, y=1),
                    Unit(unit_id="B1", side="Red", type="Tank", x=19, y=18)
                ]
            )
        ]
    )
