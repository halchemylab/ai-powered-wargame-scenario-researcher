import plotly.graph_objects as go

# Color constants
COLOR_OPEN = '#d2b48c'   # Tan
COLOR_WATER = '#4682b4'  # SteelBlue
COLOR_URBAN = '#696969'  # DimGray
COLOR_FOREST = '#228b22' # ForestGreen

# Map integer to color
TERRAIN_COLORSCALE = [
    [0.0, COLOR_OPEN],   [0.25, COLOR_OPEN],
    [0.25, COLOR_WATER], [0.5, COLOR_WATER],
    [0.5, COLOR_URBAN],  [0.75, COLOR_URBAN],
    [0.75, COLOR_FOREST], [1.0, COLOR_FOREST]
]

# Unit Icons Mapping
UNIT_ICONS = {
    "infantry": "💂",
    "tank": "🛡️",
    "armor": "🛡️",
    "artillery": "🎯",
    "recon": "👁️",
    "scout": "👁️",
    "hq": "🚩",
    "command": "🚩",
    "mechanized": "🚜",
    "default": "⏺️"
}

def render_map(terrain_map, units):
    """
    Generates a Plotly figure for the tactical map.
    
    Args:
        terrain_map (list of list of int): 20x20 grid.
        units (list of objects): List of units for the current frame. 
                                 Expected attrs: unit_id, side, x, y, type.
    
    Returns:
        go.Figure: The Plotly figure object.
    """
    
    # 1. Base Layer: Terrain Heatmap
    # Using discrete colorscale for categorical data
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=terrain_map,
        colorscale=TERRAIN_COLORSCALE,
        showscale=False, # Hide color bar
        zmin=0,
        zmax=3,
        hoverinfo='skip' # Disable hover on terrain for cleaner look
    ))

    # 2. Overlay: Units
    if units:
        x_vals = []
        y_vals = []
        texts = []
        colors = []
        hover_texts = []
        
        for unit in units:
            # Check for coordinates, adjust for 0-indexed logic if needed. 
            # Assuming 0-19 for 20x20. Plotly Heatmap x/y align with indices.
            x_vals.append(unit.x)
            y_vals.append(unit.y)
            
            # Side Color Logic
            if unit.side.lower() in ['blue', 'a']:
                color = 'blue'
            else:
                color = 'red'
            
            # Icon Logic
            u_type = unit.type.lower()
            symbol = UNIT_ICONS["default"]
            
            # Check for matches in our dictionary keys
            for key, icon in UNIT_ICONS.items():
                if key in u_type:
                    symbol = icon
                    # Prioritize specific matches? loop order matters. 
                    # Dictionary order is insertion ordered in modern Python.
                    # Given the list, "infantry" will match "mechanized infantry" if "infantry" is checked first.
                    # So we should probably check longer words or specific types if needed, 
                    # but simple iteration is okay for now. 
                    # If we want "mechanized infantry" to be "mechanized", we should put "mechanized" first or break.
                    break 

            texts.append(symbol)
            colors.append(color)
            hover_texts.append(f"{unit.side} - {unit.unit_id} ({unit.type})")

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='markers+text',
            text=texts,
            textfont=dict(size=20, color='black'), # Black icons for contrast
            marker=dict(
                size=30,
                color=colors,
                opacity=0.5, # Transparent bubble to show terrain/grid slightly
                line=dict(width=1, color='white')
            ),
            hoverinfo='text',
            hovertext=hover_texts,
            showlegend=False
        ))

    # 3. Styling
    fig.update_layout(
        width=600,
        height=600,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            showgrid=True, 
            zeroline=False, 
            visible=False, 
            range=[-0.5, 19.5],
            constrain='domain'
        ),
        yaxis=dict(
            showgrid=True, 
            zeroline=False, 
            visible=False, 
            range=[-0.5, 19.5],
            scaleanchor='x',
            scaleratio=1
        ),
        paper_bgcolor='rgba(0,0,0,0)', # Transparent background
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig
