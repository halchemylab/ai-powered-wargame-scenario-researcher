import plotly.graph_objects as go
import config

def render_map(terrain_map, units):
    """
    Generates a Plotly figure for the tactical map.
    """
    # ... existing render logic ...
    # Re-implementing simplified version to ensure no regression or creating a separate function?
    # The user instruction implies adding a NEW function.
    # But I should check if I can modify the existing one or add a new one.
    # Let's add render_map_on_mapbox separate for clarity.
    pass # Replaced by the implementation below.

def render_map_standard(terrain_map, units):
    # This is the original logic, I need to keep it if I'm not replacing the whole file content.
    # The tool replaces specific text. I will append the new function.
    pass 

def render_map_on_mapbox(terrain_map, units, center_lat, center_lon):
    """
    Renders the tactical map overlaid on a real-world Mapbox map.
    """
    # Approximate 2km x 2km box
    # 1 degree lat approx 111km. 2km = 0.018 degrees.
    # Grid is 20x20.
    # Let's say center is (lat, lon).
    # Top Left: lat + 0.009, lon - 0.009
    # Cell size approx 0.0009 degrees.
    
    scale = 0.0009 
    offset_x = center_lon - (10 * scale)
    offset_y = center_lat - (10 * scale) # Actually mapbox y is lat.
    # Grid (0,0) is usually Top-Left in 2D arrays, but Plotly Heatmap (0,0) is Bottom-Left.
    # Let's assume (0,0) is Bottom-Left for Cartesian consistency.
    
    # Generate Terrain Points
    lats = []
    lons = []
    colors = []
    
    height = len(terrain_map)
    width = len(terrain_map[0])
    
    for y in range(height):
        for x in range(width):
            t_type = terrain_map[y][x]
            # Simple mapping
            # lat = center_lat - (height/2 * scale) + (y * scale)
            # lon = center_lon - (width/2 * scale) + (x * scale)
            
            lat = offset_y + (y * scale)
            lon = offset_x + (x * scale)
            
            lats.append(lat)
            lons.append(lon)
            
            c_val = config.TERRAIN_COLORSCALE[t_type*2][1] # Get hex color
            colors.append(c_val)

    fig = go.Figure()

    # Terrain Layer (Markers)
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=15,
            color=colors,
            opacity=0.4,
            symbol='square' 
        ),
        text=[f"Terrain: {t}" for t in colors], # Placeholder
        hoverinfo='none',
        name='Terrain'
    ))

    # Unit Layer
    if units:
        u_lats = []
        u_lons = []
        u_texts = []
        u_colors = []
        
        for unit in units:
            lat = offset_y + (unit.y * scale)
            lon = offset_x + (unit.x * scale)
            u_lats.append(lat)
            u_lons.append(lon)
            u_texts.append(f"{unit.side.value} {unit.type}")
            
            color = 'blue' if unit.side == config.UnitSide.BLUE else 'red'
            u_colors.append(color)

        fig.add_trace(go.Scattermapbox(
            lat=u_lats,
            lon=u_lons,
            mode='markers+text',
            marker=go.scattermapbox.Marker(
                size=20,
                color=u_colors,
                symbol='circle'
            ),
            text=[config.UNIT_ICONS.get(u.type.lower(), "X") for u in units],
            textposition="top center",
            hovertext=u_texts,
            name='Units'
        ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=13
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=600,
        showlegend=False
    )
    
    return fig

def render_map(terrain_map, units, previous_units=None, show_arrows=True, show_labels=True):
    """
    Generates a Plotly figure for the tactical map.
    
    Args:
        terrain_map (list of list of int): N x M grid.
        units (list of objects): List of units for the current frame. 
                                 Expected attrs: unit_id, side, x, y, type.
        previous_units (list of objects, optional): List of units from the previous frame.
        show_arrows (bool): Whether to show movement vectors.
        show_labels (bool): Whether to show unit icons/text.
    
    Returns:
        go.Figure: The Plotly figure object.
    """
    
    # Calculate dimensions
    map_height = len(terrain_map)
    map_width = len(terrain_map[0]) if map_height > 0 else 20
    
    # 1. Base Layer: Terrain Heatmap
    # Using discrete colorscale for categorical data
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=terrain_map,
        colorscale=config.TERRAIN_COLORSCALE,
        showscale=False, # Hide color bar
        zmin=0,
        zmax=config.TerrainType.FOREST.value,
        hoverinfo='skip' # Disable hover on terrain for cleaner look
    ))

    # 1.5. Movement Vectors (Arrows)
    if show_arrows and previous_units and units:
        prev_map = {u.unit_id: u for u in previous_units}
        
        for unit in units:
            if unit.unit_id in prev_map:
                prev = prev_map[unit.unit_id]
                # Check if moved
                if prev.x != unit.x or prev.y != unit.y:
                    # Add arrow
                    fig.add_annotation(
                        x=unit.x,
                        y=unit.y,
                        ax=prev.x,
                        ay=prev.y,
                        xref="x",
                        yref="y",
                        axref="x",
                        ayref="y",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="white",
                        opacity=0.6
                    )

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
            if unit.side == config.UnitSide.BLUE:
                color = 'blue'
            else:
                color = 'red'
            
            # Icon Logic
            u_type = unit.type.lower()
            symbol = config.UNIT_ICONS["default"]
            
            # Check for matches in our dictionary keys
            for key, icon in config.UNIT_ICONS.items():
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
            
            # Expanded Tooltip
            tooltip = (
                f"<b>{unit.side.value} - {unit.unit_id}</b> ({unit.type})<br>"
                f"Health: {unit.health}% | Range: {unit.range}<br>"
                f"Status: {unit.status}"
            )
            hover_texts.append(tooltip)

        mode_settings = 'markers+text' if show_labels else 'markers'

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode=mode_settings,
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
            range=[-0.5, map_width - 0.5],
            constrain='domain'
        ),
        yaxis=dict(
            showgrid=True, 
            zeroline=False, 
            visible=False, 
            range=[-0.5, map_height - 0.5],
            scaleanchor='x',
            scaleratio=1
        ),
        paper_bgcolor='rgba(0,0,0,0)', # Transparent background
        plot_bgcolor='rgba(0,0,0,0)'
    )

def render_accumulated_heatmap(heatmap_grid):
    """
    Renders a heatmap of accumulated unit positions.
    """
    height = len(heatmap_grid)
    width = len(heatmap_grid[0]) if height > 0 else 20
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_grid,
        colorscale='Hot',
        showscale=True
    ))
    
    fig.update_layout(
        width=600,
        height=600,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            visible=False, 
            range=[-0.5, width - 0.5],
            constrain='domain'
        ),
        yaxis=dict(
            visible=False, 
            range=[-0.5, height - 0.5],
            scaleanchor='x',
            scaleratio=1
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
