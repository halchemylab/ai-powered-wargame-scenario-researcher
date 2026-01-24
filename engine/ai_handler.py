from typing import List, Optional
import openai
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError
import os
import json
import config
from duckduckgo_search import DDGS
from engine import validator, terrain_generator, models

# Export models for backward compatibility or direct access via ai_handler
Unit = models.Unit
CombatEvent = models.CombatEvent
Frame = models.Frame
WargameScenario = models.WargameScenario
ScenarioExtension = models.ScenarioExtension

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

def fetch_scenario(
    api_key: str, 
    context: str, 
    model: str = "gpt-4o", 
    use_search: bool = False, 
    use_mock: bool = False, 
    map_size: int = 20, 
    terrain_type: str = "Balanced",
    geo_location: str = None,
    blue_doctrine: str = "Generic",
    red_doctrine: str = "Generic"
) -> WargameScenario:
    """
    Calls OpenAI API to generate a wargame scenario. 
    Optionally augments context with web search and real-world terrain.
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
    real_terrain = None

    # 1. Real-World Terrain Fetching
    if geo_location:
        try:
            real_terrain = terrain_generator.fetch_terrain_map(geo_location, grid_size=map_size)
        except Exception as e:
            print(f"Failed to generate real terrain: {e}")
            # Continue without it, or maybe append a warning to context

    # 2. Search Integration
    if use_search:
        intel_general = search_realtime_intel(context)
        intel_orbat = search_realtime_intel(f"military order of battle unit composition {context}")
        
        final_context = f"""
        User Query: {context}
        
        LATEST INTELLIGENCE (General):
        {intel_general}
        
        ORDER OF BATTLE DATA (Specific Units):
        {intel_orbat}
        
        MANDATORY FORCE COMPOSITION:
        Use the 'ORDER OF BATTLE DATA' to populate the unit list.
        - Do NOT use generic names like 'Red Tank' if specific data (e.g., '90th Guards Tank Div') is available.
        - Mimic the actual equipment types (e.g., 'T-72B3', 'M1A2 Sepv3') found in the search results.
        - Balance the force ratios according to the report.
        """

    # 3. Prompt Construction
    
    # Doctrine Injection
    b_doc_desc = config.DOCTRINES.get(blue_doctrine, config.DOCTRINES["Generic"])
    r_doc_desc = config.DOCTRINES.get(red_doctrine, config.DOCTRINES["Generic"])
    
    doctrine_instruction = f"""
    STRATEGIC DOCTRINE:
    - BLUE FORCE ({blue_doctrine}): {b_doc_desc}
    - RED FORCE ({red_doctrine}): {r_doc_desc}
    
    You MUST simulate unit behaviors consistent with these doctrines. 
    (e.g., if 'Deep Battle', Red should mass artillery; if 'Asymmetric', Blue should ambush).
    """

    system_prompt = config.SYSTEM_PROMPT + "\n" + doctrine_instruction
    user_prompt = f"Generate a tactical scenario ({map_size}x{map_size} grid) based on this research topic: {final_context}"
    
    if real_terrain:
        # Flatten for token efficiency or just dump
        terrain_str = json.dumps(real_terrain)
        user_prompt += f"\n\nIMPORTANT: You MUST use the following pre-generated terrain map (0=Open, 1=Water, 2=Urban, 3=Forest). Place units logically within this specific terrain:\n{terrain_str}"
        system_prompt += "\nCONSTRAINT: The user has provided a fixed terrain map. You must return this exact terrain map in your response. Focus on placing units and generating tactics."
    else:
        user_prompt += f"\nTerrain Style: {terrain_type}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    max_retries = 3
    
    for attempt in range(max_retries + 1):
        try:
            completion = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=WargameScenario,
            )
            
            scenario = completion.choices[0].message.parsed
            
            # 4. Enforce Real Terrain (Override AI Hallucination)
            if real_terrain:
                scenario.terrain_map = real_terrain
            
            # Validate
            validator.validate_scenario(scenario)
            
            # Collect errors
            all_errors = []
            for i, frame in enumerate(scenario.frames):
                if frame.validation_errors:
                    for err in frame.validation_errors:
                        all_errors.append(f"Frame {i+1}: {err}")
            
            # If valid, return
            if not all_errors:
                return scenario
            
            # If errors and retries remain, loop
            if attempt < max_retries:
                error_feedback = "The generated scenario contains logic/physics violations. Please fix the following errors and regenerate:\n" + "\n".join(all_errors[:10]) # Limit feedback length
                
                # Update history
                messages.append({"role": "assistant", "content": scenario.model_dump_json()})
                messages.append({"role": "user", "content": error_feedback})
                
                # Optional: Log to console if visible
                print(f"Validation failed (Attempt {attempt+1}/{max_retries+1}). Retrying...")
            else:
                # Last attempt failed, return anyway but errors are stamped on frames
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
            # If it's the last attempt, raise
            if attempt == max_retries:
                raise RuntimeError(f"An unexpected error occurred during scenario generation: {str(e)}")
    
    return scenario

def ask_commander(api_key: str, scenario: WargameScenario, frame_idx: int, question: str, model: str = "gpt-4o") -> str:
    """
    Answers a question about the scenario.
    """
    if not api_key:
        return "Please provide an API Key to use the Commander's Assistant."
        
    client = openai.Client(api_key=api_key)
    
    frame = scenario.frames[frame_idx]
    
    prompt = f"""
Current Tactical Situation (Frame {frame_idx + 1}):
    - Description: {frame.frame_description}
    - Units: {json.dumps([u.model_dump() for u in frame.unit_positions])}
    - Events: {json.dumps([e.model_dump() for e in frame.combat_log])}
    
    Question: {question}
    """
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a tactical advisor. Answer the question based ONLY on the provided simulation state. Be concise and professional."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"