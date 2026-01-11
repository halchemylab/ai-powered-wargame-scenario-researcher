import streamlit as st
import os
import time
from dotenv import load_dotenv
from engine import ai_handler, map_renderer
from utils import state_manager, exporter

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Wargame Researcher",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize State
state_manager.initialize_state()

# --- Sidebar ---
with st.sidebar:
    st.header("Control Panel")
    
    # Metrics
    st.subheader("Session Metrics")
    col1, col2 = st.columns(2)
    col1.metric("Scenarios", st.session_state.total_scenarios_run)
    col2.metric("Frames", st.session_state.total_frames_generated)
    
    st.divider()
    
    # API Key
    default_key = os.getenv("OPENAI_API_KEY", "")
    api_key = st.text_input(
        "OpenAI API Key", 
        value=default_key, 
        type="password",
        help="Enter your OpenAI API key to generate scenarios."
    )
    
    # Model Selection
    model_name = st.text_input(
        "AI Model", 
        value="gpt-4o", 
        help="Change to 'gpt-5.2-preview' (or similar) if you have access. Default is 'gpt-4o'."
    )
    
    st.caption("AI Model: Structured Outputs Enabled")

# --- Main Area ---
st.title("AI-Powered Wargame Scenario Researcher")
st.markdown("Generates tactical simulations on a 20x20 grid based on real-world research topics.")

# Input Section
with st.container():
    col_input, col_opt = st.columns([3, 1])
    
    with col_input:
        context_input = st.text_area(
            "Scenario Context / Research Topic",
            placeholder="E.g., Recent skirmishes in the Avdiivka sector...",
            height=100
        )
    
    with col_opt:
        st.write("") # Spacer
        st.write("") # Spacer
        use_search = st.checkbox(
            "Enable Real-Time Data", 
            value=False,
            help="Searches the web for the latest news on the topic before generating the simulation."
        )
    
    if st.button("Generate Simulation", type="primary"):
        if not api_key:
            st.error("Please provide an OpenAI API Key.")
        elif not context_input:
            st.warning("Please enter a research topic.")
        else:
            with st.spinner("Analyzing tactics and generating scenario..."):
                try:
                    # Call AI Handler
                    scenario = ai_handler.fetch_scenario(
                        api_key, 
                        context_input, 
                        model=model_name, 
                        use_search=use_search
                    )
                    
                    # Update State
                    state_manager.set_scenario(scenario)
                    st.success("Simulation generated successfully!")
                    time.sleep(1) # Brief pause for UX
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating scenario: {e}")

st.divider()

# Visualization Section
if st.session_state.current_scenario:
    scenario = st.session_state.current_scenario
    current_idx = st.session_state.current_frame_index
    total_frames = len(scenario.frames)
    
    # Get current frame data
    current_frame = scenario.frames[current_idx]
    
    # Layout: Map on Left, Info on Right
    col_map, col_info = st.columns([2, 1])
    
    with col_map:
        st.subheader(f"Tactical Map - Frame {current_idx + 1}/{total_frames}")
        fig = map_renderer.render_map(
            scenario.terrain_map, 
            current_frame.unit_positions
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_info:
        st.subheader("Situation Brief")
        st.info(current_frame.frame_description)
        
        st.subheader("Controls")
        c1, c2, c3 = st.columns([1, 1, 2])
        
        with c1:
            if st.button("◀ Prev"):
                state_manager.prev_frame()
                st.rerun()
                
        with c2:
            if st.button("Next ▶"):
                state_manager.next_frame()
                st.rerun()
        
        st.markdown("---")
        
        # Export
        report_md = exporter.generate_markdown_report(scenario)
        st.download_button(
            label="Download Commander's Journal",
            data=report_md,
            file_name="commanders_journal.md",
            mime="text/markdown"
        )
        
else:
    st.info("Enter a context above and click 'Generate Simulation' to begin.")

# Footer
st.markdown("---")
st.caption("AI-Powered Wargame Scenario Researcher | v1.0")
