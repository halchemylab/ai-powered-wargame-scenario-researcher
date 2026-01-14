import streamlit as st
import os
import time
import json
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

    # Save/Load
    with st.expander("💾 Save/Load Scenario", expanded=False):
        uploaded_file = st.file_uploader("Load JSON Scenario", type=["json"])
        if uploaded_file is not None:
            try:
                # Read and parse
                json_data = uploaded_file.getvalue().decode("utf-8")
                loaded_scenario = ai_handler.WargameScenario.model_validate_json(json_data)
                state_manager.load_existing_scenario(loaded_scenario)
                st.success("Scenario loaded!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Invalid file: {e}")

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
    
    st.divider()
    
    # Map Configuration
    st.subheader("Scenario Settings")
    map_size = st.slider("Grid Size", min_value=10, max_value=40, value=20, step=5, help="Size of the battlefield (NxN).")
    terrain_type = st.selectbox(
        "Terrain Style", 
        ["Balanced", "Open Plains", "Dense Urban", "Forest Heavy", "Water/Islands", "Desert"],
        index=0
    )
    
    use_mock = st.checkbox(
        "Enable Offline / Mock Mode",
        value=False,
        help="Use pre-generated data for testing without API usage."
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
        if not api_key and not use_mock:
            st.error("Please provide an OpenAI API Key.")
        elif not context_input and not use_mock:
            st.warning("Please enter a research topic.")
        else:
            with st.spinner("Analyzing tactics and generating scenario..."):
                try:
                    # Call AI Handler
                    scenario = ai_handler.fetch_scenario(
                        api_key, 
                        context_input, 
                        model=model_name, 
                        use_search=use_search,
                        use_mock=use_mock,
                        map_size=map_size,
                        terrain_type=terrain_type
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
        report_pdf = exporter.generate_pdf_report(scenario)
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.download_button(
                label="📄 Journal (MD)",
                data=report_md,
                file_name="commanders_journal.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="📕 Journal (PDF)",
                data=report_pdf,
                file_name="commanders_journal.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_dl3:
            st.download_button(
                label="💾 Scenario (JSON)",
                data=scenario.model_dump_json(indent=2),
                file_name="wargame_scenario.json",
                mime="application/json",
                use_container_width=True
            )
        
else:
    st.info("Enter a context above and click 'Generate Simulation' to begin.")

# Footer
st.markdown("---")
st.caption("AI-Powered Wargame Scenario Researcher | v1.0")
