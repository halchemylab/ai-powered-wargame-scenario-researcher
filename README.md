# AI-Powered Wargame Scenario Researcher 🗺️🤖

A modular Streamlit application that leverages OpenAI's GPT-4o with **Structured Outputs** to generate, visualize, and analyze tactical wargame scenarios. Designed for researchers and hobbyists to explore "What-If" military maneuvers on a dynamic grid.

## 🚀 Features

### 🧠 AI-Driven Simulation
- **Contextual Generation:** Create scenarios from natural language prompts (e.g., "Urban defense in Avdiivka").
- **Structured Tactics:** Uses GPT-4o to generate spatially consistent unit movements and terrain.
- **Strategic Doctrines:** Apply specific combat styles like *NATO Combined Arms*, *Soviet Deep Battle*, or *Asymmetric Warfare*.
- **Real-Time Data:** Optional web-search integration to incorporate latest news into simulations.

### 🗺️ Interactive Visualization
- **Tactical Map:** 2D grid visualization with terrain types (Open, Water, Urban, Forest) and unit overlays.
- **Geospatial Overlay:** Map tactical grids onto real-world locations using OpenStreetMap.
- **Playback Controls:** Step-by-step timeline navigation with auto-play and movement vectors (arrows).
- **Battlefield Editor:** Live-edit unit positions, health, and terrain directly on the map.

### 📈 Analysis & Branching
- **What-If Branching:** Modify the current state and regenerate a new timeline from that point.
- **After-Action Analytics:** View force correlation (attrition) charts and zone-of-control heatmaps.
- **Commander's Chat:** AI assistant to answer tactical questions about the ongoing simulation.

### 💾 Export & Integration
- **Commander's Journal:** Export full scenario briefings as Markdown or PDF.
- **VTT Export:** Generic JSON export compatible with Virtual Tabletops.
- **Session Persistence:** Save and load full scenario states via JSON.

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Visualization:** [Plotly](https://plotly.com/python/)
- **AI Engine:** [OpenAI API](https://openai.com/api/) (Structured Outputs, GPT-4o)
- **Data Handling:** [Pydantic](https://docs.pydantic.dev/), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Geospatial:** [GeoPy](https://geopy.readthedocs.io/), [Overpy](https://python-overpy.readthedocs.io/)
- **Reporting:** [FPDF2](https://pyfpdf.github.io/fpdf2/)

## ⚙️ Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/ai-powered-wargame-scenario-researcher.git
    cd ai-powered-wargame-scenario-researcher
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up API Keys:**
    - Create a `.env` file in the root directory:
      ```env
      OPENAI_API_KEY=your_openai_api_key_here
      ```
    - *Optional:* You can also enter the API key directly in the application sidebar.

## 📖 Usage

1.  **Start the Application:**
    ```bash
    streamlit run app.py
    ```
2.  **Configure Scenario:**
    - Enter a research topic or use one of the quick-start templates.
    - Adjust grid size, terrain style, and force doctrines in the sidebar.
    - (Optional) Enter a real-world location for geospatial overlay.
3.  **Interact:**
    - Use the **Timeline Slider** to navigate the battle.
    - Use the **Battlefield Editor** to tweak the simulation.
    - Click **Regenerate Future Frames** to explore alternative outcomes.

## 📂 Project Structure

- `app.py`: Main Streamlit dashboard and UI logic.
- `engine/`: Core simulation logic.
    - `ai_handler.py`: OpenAI integration and scenario continuation.
    - `map_renderer.py`: Plotly and Mapbox visualization.
    - `analytics.py`: Attrition and heatmap calculations.
    - `validator.py`: Spatial and logical consistency checks.
- `utils/`: Utilities.
    - `state_manager.py`: Session state and persistence.
    - `exporter.py`: PDF/Markdown/JSON report generation.
- `tests/`: Automated test suite using `pytest`.

## 🧪 Testing

Run the test suite to ensure engine consistency:
```bash
pytest
```

---
*Developed for tactical research and simulation exploration.*