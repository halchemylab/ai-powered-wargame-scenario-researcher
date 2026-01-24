from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import config

class Unit(BaseModel):
    unit_id: str = Field(..., description="Unique identifier for the unit (e.g., 'A-1', 'B-Tank').")
    side: config.UnitSide = Field(..., description="The side the unit belongs to.")
    type: str = Field(..., description="Type of unit (e.g., Infantry, Tank, Artillery).")
    x: int = Field(..., ge=0, description="X coordinate on the grid.")
    y: int = Field(..., ge=0, description="Y coordinate on the grid.")
    health: int = Field(100, ge=0, le=100, description="Unit health percentage.")
    range: int = Field(1, ge=1, description="Effective firing range in grid cells.")
    status: str = Field("Active", description="Current tactical status (e.g., 'Moving', 'Engaged', 'Digging In').")

class CombatEvent(BaseModel):
    source_unit_id: str = Field(..., description="ID of the unit initiating the action.")
    target_unit_id: Optional[str] = Field(None, description="ID of the target unit, if applicable.")
    action_type: Literal["Move", "Fire", "Suppression", "Retreat", "Reinforce", "Intel"] = Field(..., description="Type of combat event.")
    details: str = Field(..., description="Short description of the event (e.g. 'Fired 120mm shell', 'Moved to Grid (4,5)').")
    outcome: Optional[str] = Field(None, description="Result of the action (e.g., 'Target Hit (15 dmg)', 'Missed').")

class Frame(BaseModel):
    frame_description: str = Field(..., description="Narrative description of the tactical situation in this time step.")
    unit_positions: List[Unit] = Field(..., description="List of all units and their positions in this frame.")
    combat_log: List[CombatEvent] = Field(default_factory=list, description="List of specific tactical events occurring in this frame.")
    validation_errors: List[str] = Field(default_factory=list, description="Logic/Physics violations detected in this frame.")

class WargameScenario(BaseModel):
    terrain_map: List[List[int]] = Field(..., description="N x N integer matrix representing terrain. 0: Open, 1: Water, 2: Urban, 3: Forest.")
    frames: List[Frame] = Field(..., description="Sequential frames depicting the tactical movement.")

class ScenarioExtension(BaseModel):
    frames: List[Frame] = Field(..., description="Sequential frames continuing the tactical movement.")
