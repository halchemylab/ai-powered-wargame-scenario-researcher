from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import openai
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError
import os
import json
import config
from duckduckgo_search import DDGS

# --- Data Models ---

class Unit(BaseModel):
    unit_id: str = Field(..., description="Unique identifier for the unit (e.g., 'A-1', 'B-Tank').")
    side: config.UnitSide = Field(..., description="The side the unit belongs to.")
    type: str = Field(..., description="Type of unit (e.g., Infantry, Tank, Artillery).")
    x: int = Field(..., ge=0, description="X coordinate on the grid.")
    y: int = Field(..., ge=0, description="Y coordinate on the grid.")
    health: int = Field(100, ge=0, le=100, description="Unit health percentage.")
    range: int = Field(1, ge=1, description="Effective firing range in grid cells.")
    status: str = Field("Active", description="Current tactical status (e.g., 'Moving', 'Engaged', 'Digging In').")

class Frame(BaseModel):
    frame_description: str = Field(..., description="Narrative description of the tactical situation in this time step.")
    unit_positions: List[Unit] = Field(..., description="List of all units and their positions in this frame.")

class WargameScenario(BaseModel):
    terrain_map: List[List[int]] = Field(..., description="N x N integer matrix representing terrain. 0: Open, 1: Water, 2: Urban, 3: Forest.")
    frames: List[Frame] = Field(..., description="Sequential frames depicting the tactical movement.")

class ScenarioExtension(BaseModel):
    frames: List[Frame] = Field(..., description="Sequential frames continuing the tactical movement.")

# --- Logic ---

def search_realtime_intel(query: str, max_results: int = 5) -> str:
    """
    Searches DuckDuckGo for real-time information on the topic.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No real-time data found."
        
        # Compile snippets
        intel_report = "REAL-TIME INTELLIGENCE REPORT:\n"
        for i, res in enumerate(results):
            intel_report += f"{i+1}. {res['title']}: {res['body']}\n"
        
        return intel_report
    except Exception as e:
        return f"Warning: Could not fetch real-time data ({str(e)}). Proceeding with internal knowledge only."

def continue_scenario(api_key: str, current_scenario: WargameScenario, current_frame_idx: int, context: str, model: str = "gpt-4o") -> List[Frame]:
    """
    Generates new frames continuing from the specified frame index.
    """
    if not api_key:
        raise ValueError("OpenAI API Key is missing.")

    client = openai.Client(api_key=api_key)

    # Prepare context
    last_frame = current_scenario.frames[current_frame_idx]
    
    # Serialize terrain and units for the prompt
    # Simplified terrain representation to save tokens/complexity if needed, but 20x20 is small enough.
    
    prompt = f"""
    **Mission Update:**
    The user has intervened or requested a branch from Frame {current_frame_idx + 1}.
    
    **Context:**
    {context}
    
    **Current Tactical Situation (Frame {current_frame_idx + 1}):**
    - Units: {json.dumps([u.model_dump() for u in last_frame.unit_positions])}
    
    **Task:**
    Generate 5 NEW frames continuing from this exact state. 
    Maintain unit IDs. 
    Respect the terrain (0=Open, 1=Water, 2=Urban, 3=Forest).
    """

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT + "\nIMPORTANT: You are CONTINUING an existing battle. Do not regenerate terrain. Only generate the 'frames' list."},
                {"role": "user", "content": prompt},
            ],
            response_format=ScenarioExtension,
        )
        
        extension = completion.choices[0].message.parsed
        return extension.frames

    except Exception as e:
        raise RuntimeError(f"Error extending scenario: {str(e)}")

def fetch_scenario(api_key: str, context: str, model: str = "gpt-4o", use_search: bool = False, use_mock: bool = False, map_size: int = 20, terrain_type: str = "Balanced") -> WargameScenario:
    """
    Calls OpenAI API to generate a wargame scenario. 
    Optionally augments context with web search.
    """
    if use_mock:
        try:
            # Load from engine/mock_data.json
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mock_path = os.path.join(current_dir, "mock_data.json")
            
            with open(mock_path, "r") as f:
                data = json.load(f)
            
            # Validate with Pydantic
            scenario = WargameScenario(**data)
            # Add a note to the first frame description so the user knows
            scenario.frames[0].frame_description = "[MOCK MODE] " + scenario.frames[0].frame_description
            return scenario
        except Exception as e:
            raise RuntimeError(f"Failed to load mock data: {str(e)}")

    if not api_key:
         raise ValueError("OpenAI API Key is missing.")

    client = openai.Client(api_key=api_key)
    
    final_context = context

    if use_search:
        intel = search_realtime_intel(context)
        final_context = f"""
        User Query: {context}
        
        LATEST INTELLIGENCE (Real-Time Search):
        {intel}
        
        Based on the intelligence above, reconstruct the tactical situation.
        """

    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a tactical scenario ({map_size}x{map_size} grid, {terrain_type} terrain) based on this research topic: {final_context}"},
            ],
            response_format=WargameScenario,
        )
        
        scenario = completion.choices[0].message.parsed
        return scenario

    except AuthenticationError:
        raise ValueError("Invalid OpenAI API Key. Please check your credentials.")
    except RateLimitError:
        raise RuntimeError("OpenAI API rate limit exceeded. Please try again later.")
    except APIConnectionError:
        raise RuntimeError("Failed to connect to OpenAI API. Please check your internet connection.")
    except APIError as e:
        raise RuntimeError(f"OpenAI API returned an error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during scenario generation: {str(e)}")
