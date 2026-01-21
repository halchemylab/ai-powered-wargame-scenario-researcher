import streamlit as st
import os
import time
import json
import config
from dotenv import load_dotenv
from engine import ai_handler, map_renderer, analytics, validator
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
    
    # Geo Input
    st.markdown("#### 🌍 Geospatial Overlay")
    geo_location = st.text_input("Real-World Location", placeholder="e.g., Avdiivka, Ukraine", help="Enter a city or region to overlay the grid on a real map.")
    
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
        # Quick-Start Templates
        def set_template(text):
            st.session_state.scenario_input = text
            
        st.write(" **Quick Start Templates:**")
        t1, t2, t3 = st.columns(3)
        with t1: 
            st.button("🏙️ Urban Defense", on_click=set_template, args=("Urban warfare in a dense city center. Blue team defending key intersections against Red armored advance.",), use_container_width=True)
        with t2:
            st.button("🌉 River Crossing", on_click=set_template, args=("Red forces attempting a pontoon crossing under fire from Blue artillery in open terrain.",), use_container_width=True)
        with t3:
            st.button("🌲 Forest Ambush", on_click=set_template, args=("Meeting engagement in dense forest. Recon units clashing in low visibility conditions.",), use_container_width=True)

        context_input = st.text_area(
            "Scenario Context / Research Topic",
            placeholder="E.g., Recent skirmishes in the Avdiivka sector...",
            height=100,
            key="scenario_input"
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
                    
                    # Validate
                    validator.validate_scenario(scenario)
                    
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
    
    tab_sim, tab_anl = st.tabs(["Tactical View", "Analytics & AAR"])
    
    with tab_sim:
        # Layout: Map on Left, Info on Right
        col_map, col_info = st.columns([2, 1])
        
        with col_map:
            st.subheader(f"Tactical Map - Frame {current_idx + 1}/{total_frames}")
            
            # Geo-Coding Logic
            coords = None
            if geo_location and not use_mock:
                try:
                    from geopy.geocoders import Nominatim
                    geolocator = Nominatim(user_agent="wargame_researcher_v1")
                    location = geolocator.geocode(geo_location)
                    if location:
                        coords = (location.latitude, location.longitude)
                        st.caption(f"📍 Overlaying on: {location.address}")
                except Exception as e:
                    st.warning(f"Could not find location: {e}")
            
            if coords:
                fig = map_renderer.render_map_on_mapbox(
                    scenario.terrain_map,
                    current_frame.unit_positions,
                    coords[0],
                    coords[1]
                )
            else:
                prev_units = None
                if current_idx > 0:
                    prev_units = scenario.frames[current_idx-1].unit_positions

                fig = map_renderer.render_map(
                    scenario.terrain_map, 
                    current_frame.unit_positions,
                    previous_units=prev_units
                )
            
            # Enable selection events to capture clicks
            map_event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points", key="tactical_map_chart")
            
            # Process selection if user clicked the map
            if map_event and "selection" in map_event and map_event["selection"]["points"]:
                clicked_point = map_event["selection"]["points"][0]
                new_x = int(clicked_point["x"])
                new_y = int(clicked_point["y"])
                
                # Check if changed
                if new_x != st.session_state.get("editor_x") or new_y != st.session_state.get("editor_y"):
                    st.session_state["editor_x"] = new_x
                    st.session_state["editor_y"] = new_y
                    
                    # Pre-fill Unit Editor
                    found = next((u for u in current_frame.unit_positions if u.x == new_x and u.y == new_y), None)
                    if found:
                        st.session_state["u_id_input"] = found.unit_id
                        st.session_state["u_status_input"] = found.status
                        st.session_state["u_side_idx_input"] = 0 if found.side == config.UnitSide.BLUE else 1
                        
                        types = ["Infantry", "Tank", "Mechanized", "Recon", "Artillery", "HQ"]
                        try:
                            st.session_state["u_type_idx_input"] = types.index(found.type) 
                        except ValueError:
                            st.session_state["u_type_idx_input"] = 0
                    else:
                        # Reset
                        st.session_state["u_id_input"] = f"Unit-{new_x}-{new_y}"
                        st.session_state["u_status_input"] = "Active"
                        st.session_state["u_side_idx_input"] = 0
                        st.session_state["u_type_idx_input"] = 0
                    
                    st.rerun()
            
        with col_info:
            st.subheader("Situation Brief")
            st.info(current_frame.frame_description)
            
            # --- Validation Alerts ---
            if hasattr(current_frame, 'validation_errors') and current_frame.validation_errors:
                for err in current_frame.validation_errors:
                    st.error(f"⚠️ Logic Violation: {err}")
            
            # --- Combat Log ---
            if hasattr(current_frame, 'combat_log') and current_frame.combat_log:
                with st.expander("📜 Combat Log / Events", expanded=True):
                    for event in current_frame.combat_log:
                        # Icon Mapping
                        icon = "⚔️"
                        if event.action_type == "Move": icon = "🦶"
                        elif event.action_type == "Fire": icon = "🔥"
                        elif event.action_type == "Retreat": icon = "🏳️"
                        elif event.action_type == "Intel": icon = "📡"
                        
                        st.markdown(
                            f"**{icon} {event.source_unit_id}** "
                            f"_{event.action_type}_ -> "
                            f"**{event.target_unit_id or ''}** "
                            f": {event.details} "
                            f"**{f'[{event.outcome}]' if event.outcome else ''}**"
                        )
            
            st.subheader("Controls")
            
            # Interactive Timeline Slider
            def update_timeline():
                st.session_state.current_frame_index = st.session_state.timeline_slider

            st.slider(
                "Timeline Navigation",
                min_value=0,
                max_value=total_frames - 1,
                value=current_idx,
                key="timeline_slider",
                on_change=update_timeline,
                help="Drag to jump to any point in the simulation."
            )
            
            # Playback Controls (Optional simplified version)
            pc1, pc2, pc3 = st.columns([1, 1, 2])
            with pc1:
                if st.button("⏪ Start"):
                    st.session_state.current_frame_index = 0
                    st.rerun()
            with pc2:
                if st.button("End ⏩"):
                    st.session_state.current_frame_index = total_frames - 1
                    st.rerun()
            
            st.markdown("---")

            # --- Battlefield Editor ---
            with st.expander("🛠️ Battlefield Editor", expanded=False):
                st.caption(f"Edit Frame {current_idx + 1} at (X, Y)")
                
                # 1. Coordinate Selection
                # Initialize selection state if needed
                if "editor_x" not in st.session_state: st.session_state.editor_x = 0
                if "editor_y" not in st.session_state: st.session_state.editor_y = 0

                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_x = st.number_input("Grid X", 0, len(scenario.terrain_map[0])-1, key="editor_x")
                with ec2:
                    edit_y = st.number_input("Grid Y", 0, len(scenario.terrain_map)-1, key="editor_y")
                
                # Context at Coords
                found_unit = next((u for u in current_frame.unit_positions if u.x == edit_x and u.y == edit_y), None)
                current_terrain = scenario.terrain_map[edit_y][edit_x]

                st.divider()

                # 2. Terrain Editing
                st.subheader("Terrain")
                tc1, tc2 = st.columns([3, 1])
                with tc1:
                    new_terrain = st.selectbox(
                        "Set Terrain Type",
                        options=[t.value for t in config.TerrainType],
                        format_func=lambda x: config.TerrainType(x).name,
                        index=int(current_terrain),
                        key=f"terrain_sel_{edit_x}_{edit_y}"
                    )
                with tc2:
                    st.write("") # Spacer
                    st.write("") 
                    if st.button("Set", key="btn_set_terrain"):
                        scenario.terrain_map[edit_y][edit_x] = new_terrain
                        st.rerun()

                st.divider()

                # 3. Unit Editing
                st.subheader("Unit")
                if found_unit:
                    st.info(f"Present: {found_unit.side.value} {found_unit.type} ({found_unit.unit_id})")
                else:
                    st.caption("No unit at this location.")
                
                # Init State if not present
                if "u_side_idx_input" not in st.session_state: st.session_state.u_side_idx_input = 0
                if "u_type_idx_input" not in st.session_state: st.session_state.u_type_idx_input = 0
                if "u_id_input" not in st.session_state: st.session_state.u_id_input = "New-Unit"
                if "u_status_input" not in st.session_state: st.session_state.u_status_input = "Active"

                uc1, uc2 = st.columns(2)
                with uc1:
                    u_side = st.selectbox("Side", ["Blue", "Red"], key="u_side_idx_input")
                    u_type = st.selectbox("Type", ["Infantry", "Tank", "Mechanized", "Recon", "Artillery", "HQ"], key="u_type_idx_input")
                with uc2:
                    u_id = st.text_input("Unit ID", key="u_id_input")
                    u_status = st.text_input("Status", key="u_status_input")
                
                # Update logic requires reading from the WIDGET keys or State?
                # st.session_state["u_id_input"] holds the current value.
                
                uc3, uc4 = st.columns(2)
                with uc3:
                    if st.button("Place / Update Unit", type="primary"):
                        # Remove existing if present to avoid dupes
                        if found_unit:
                            current_frame.unit_positions.remove(found_unit)
                        
                        new_unit = ai_handler.Unit(
                            unit_id=st.session_state.u_id_input,
                            side=config.UnitSide(u_side), # Read from variable bound to selectbox
                            type=u_type,
                            x=edit_x,
                            y=edit_y,
                            health=found_unit.health if found_unit else 100,
                            range=found_unit.range if found_unit else 3,
                            status=st.session_state.u_status_input
                        )
                        current_frame.unit_positions.append(new_unit)
                        st.rerun()
                with uc4:
                    if found_unit:
                        if st.button("🗑️ Remove Unit", type="secondary"):
                            current_frame.unit_positions.remove(found_unit)
                            st.rerun()

            st.markdown("---")
            
            # --- Branching / What-If ---
            with st.expander("🔀 Scenario Branching (What-If)", expanded=False):
                st.info("Modify the battlefield above, then generate a NEW timeline from this point.")
                branch_context = st.text_input("Reason for Branch / New Orders", placeholder="e.g., Red tank forces breakthrough...")
                
                if st.button("Regenerate Future Frames", type="primary"):
                    if not api_key:
                        st.error("API Key required.")
                    else:
                        with st.spinner("Calculating alternative timeline..."):
                            try:
                                # 1. Truncate
                                scenario.frames = scenario.frames[:current_idx+1]
                                
                                # 2. Generate Extension
                                new_frames = ai_handler.continue_scenario(
                                    api_key,
                                    scenario,
                                    current_idx,
                                    branch_context or "Continue the battle from this new state.",
                                    model=model_name
                                )
                                
                                # 3. Append
                                scenario.frames.extend(new_frames)
                                
                                # Validate Full Scenario
                                validator.validate_scenario(scenario)

                                st.session_state.total_frames_generated += len(new_frames)
                                st.success(f"Branch created! Added {len(new_frames)} new frames.")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Branching failed: {e}")

            st.markdown("---")

            # Export
            report_md = exporter.generate_markdown_report(scenario)
            report_pdf = exporter.generate_pdf_report(scenario)
            vtt_json = exporter.generate_vtt_json(scenario)
            
            col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
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
            with col_dl4:
                st.download_button(
                    label="🎲 VTT Export",
                    data=vtt_json,
                    file_name="vtt_scenario.json",
                    mime="application/json",
                    use_container_width=True,
                    help="Generic JSON format for Virtual Tabletop imports."
                )
    
    with tab_anl:
        st.header("After-Action Analytics")
        
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.subheader("Force Correlation (Attrition)")
            df_corr = analytics.calculate_force_correlation(scenario)
            st.line_chart(df_corr)
            st.caption("Unit counts per side over time.")
            
        with col_a2:
            st.subheader("Zone of Control Heatmap")
            heatmap_data = analytics.calculate_heatmap(scenario)
            fig_heat = map_renderer.render_accumulated_heatmap(heatmap_data)
            st.plotly_chart(fig_heat, use_container_width=True)
            st.caption("Accumulated unit presence per grid sector.")
        
else:
    st.info("Enter a context above and click 'Generate Simulation' to begin.")

# Footer
st.markdown("---")
st.caption("AI-Powered Wargame Scenario Researcher | v1.0")
