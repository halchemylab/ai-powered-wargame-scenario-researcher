import streamlit as st

def initialize_state():
    """Initializes session state variables if they don't exist."""
    
    # Metrics
    if 'total_frames_generated' not in st.session_state:
        st.session_state.total_frames_generated = 0
    if 'total_scenarios_run' not in st.session_state:
        st.session_state.total_scenarios_run = 0
        
    # Scenario Data
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = None # Holds the full JSON object
    
    # Navigation
    if 'current_frame_index' not in st.session_state:
        st.session_state.current_frame_index = 0

def update_metrics(num_frames):
    """Updates the persistent metrics."""
    st.session_state.total_scenarios_run += 1
    st.session_state.total_frames_generated += num_frames

def set_scenario(scenario_data):
    """Sets the new scenario and resets navigation."""
    st.session_state.current_scenario = scenario_data
    st.session_state.current_frame_index = 0
    update_metrics(len(scenario_data.frames))

def load_existing_scenario(scenario_data):
    """Sets a loaded scenario without incrementing generation metrics."""
    st.session_state.current_scenario = scenario_data
    st.session_state.current_frame_index = 0

def next_frame():
    """Advances to the next frame if possible."""
    if st.session_state.current_scenario and st.session_state.current_frame_index < len(st.session_state.current_scenario.frames) - 1:
        st.session_state.current_frame_index += 1

def prev_frame():
    """Goes back to the previous frame if possible."""
    if st.session_state.current_scenario and st.session_state.current_frame_index > 0:
        st.session_state.current_frame_index -= 1
