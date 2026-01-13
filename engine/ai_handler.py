from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import openai
import os
import json
import config
from duckduckgo_search import DDGS

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
        return f"Error fetching real-time data: {str(e)}"

def fetch_scenario(api_key: str, context: str, model: str = "gpt-4o", use_search: bool = False) -> WargameScenario:
    """
    Calls OpenAI API to generate a wargame scenario. 
    Optionally augments context with web search.
    """
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
                {"role": "user", "content": f"Generate a tactical scenario based on this research topic: {final_context}"},
            ],
            response_format=WargameScenario,
        )
        
        scenario = completion.choices[0].message.parsed
        return scenario

    except Exception as e:
        # In a real app, you might want to log this or return a specific error structure
        raise RuntimeError(f"AI Generation failed: {str(e)}")
