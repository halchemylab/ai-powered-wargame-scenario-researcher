from pydantic import BaseModel, Field
from typing import List, Literal
import openai
import os
import json

# --- Data Models ---

class Unit(BaseModel):
    unit_id: str = Field(..., description="Unique identifier for the unit (e.g., 'A-1', 'B-Tank').")
    side: Literal['Blue', 'Red'] = Field(..., description="The side the unit belongs to.")
    type: str = Field(..., description="Type of unit (e.g., Infantry, Tank, Artillery).")
    x: int = Field(..., ge=0, le=19, description="X coordinate on the 20x20 grid (0-19).")
    y: int = Field(..., ge=0, le=19, description="Y coordinate on the 20x20 grid (0-19).")

class Frame(BaseModel):
    frame_description: str = Field(..., description="Narrative description of the tactical situation in this time step.")
    unit_positions: List[Unit] = Field(..., description="List of all units and their positions in this frame.")

class WargameScenario(BaseModel):
    terrain_map: List[List[int]] = Field(..., description="20x20 integer matrix representing terrain. 0: Open, 1: Water, 2: Urban, 3: Forest.")
    frames: List[Frame] = Field(..., description="Sequential frames depicting the tactical movement.")

# --- Logic ---

SYSTEM_PROMPT = """
You are an expert military simulation engine. Your task is to generate realistic tactical wargame scenarios based on a user's research topic.

**Output Format:**
You must output a valid JSON object matching the provided schema.

**Constraints & Rules:**
1.  **Grid:** The map is a 20x20 grid. Coordinates are (0,0) to (19,19).
2.  **Terrain:** Generate a tactical terrain map (20x20 matrix) using integers: 
    *   0: Open Ground (plains, desert)
    *   1: Water (rivers, lakes)
    *   2: Urban (buildings, towns)
    *   3: Forest (woods, jungle)
    Make the terrain tactically interesting (chokepoints, cover).
3.  **Sides:** Use 'Blue' (Side A) and 'Red' (Side B).
4.  **Movement Physics (Spatial Consistency):** 
    *   Units CANNOT teleport.
    *   Between consecutive frames, a unit can move a MAXIMUM of 2 squares (Euclidean distance approx, or 2 steps).
    *   Units cannot move into Deep Water (1) unless they are amphibious (context dependent, generally avoid).
5.  **Consistency:** Unit IDs must remain constant across frames. If a unit is destroyed, remove it from the list in subsequent frames.
6.  **Narrative:** The `frame_description` should briefly explain the maneuver (e.g., "Red forces flank left while Blue holds the urban center.").

**Task:**
Generate a scenario with 5-10 frames based on the user's input context.
"""

def fetch_scenario(api_key: str, context: str, model: str = "gpt-4o") -> WargameScenario:
    """
    Calls OpenAI API to generate a wargame scenario.
    """
    client = openai.Client(api_key=api_key)

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a tactical scenario based on this research topic: {context}"},
            ],
            response_format=WargameScenario,
        )
        
        scenario = completion.choices[0].message.parsed
        return scenario

    except Exception as e:
        # In a real app, you might want to log this or return a specific error structure
        raise RuntimeError(f"AI Generation failed: {str(e)}")
