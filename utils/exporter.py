import pandas as pd
import io

def generate_markdown_report(scenario_data):
    """
    Generates a Markdown report ('Commander's Journal') from the scenario frames.
    
    Args:
        scenario_data: The Pydantic model or dictionary containing 'frames'.
                       Expected structure has a .frames attribute which is a list.
    
    Returns:
        str: The complete Markdown string.
    """
    if not scenario_data or not scenario_data.frames:
        return "# Commander's Journal\n\nNo data available."

    lines = ["# Commander's Journal", ""]
    
    lines.append("## Tactical Summary")
    lines.append(f"**Total Frames:** {len(scenario_data.frames)}")
    lines.append("---")
    
    for i, frame in enumerate(scenario_data.frames):
        lines.append(f"### Frame {i + 1}")
        lines.append(f"**Situation:** {frame.frame_description}")
        
        # Optional: Add unit summary table for this frame if desired
        if hasattr(frame, 'unit_positions') and frame.unit_positions:
            lines.append("\n**Unit Dispositions:**")
            # Create a simple table
            header = "| Unit ID | Side | Position (X,Y) |"
            sep = "|---|---|---|"
            lines.append(header)
            lines.append(sep)
            
            for unit in frame.unit_positions:
                # Handle coordinates safely
                pos_str = f"({unit.x}, {unit.y})"
                lines.append(f"| {unit.unit_id} | {unit.side} | {pos_str} |")
        
        lines.append("\n---")
    
    return "\n".join(lines)
