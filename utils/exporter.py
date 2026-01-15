import pandas as pd
import io
import json
from fpdf import FPDF
import config

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, "Commander's Journal", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_vtt_json(scenario) -> str:
    """
    Generates a generic VTT-compatible JSON.
    Includes map dimensions, terrain data, and unit tokens.
    """
    height = len(scenario.terrain_map)
    width = len(scenario.terrain_map[0]) if height > 0 else 0
    
    # Structure suitable for import scripts or custom VTT modules
    vtt_data = {
        "format_version": "1.0",
        "map": {
            "width": width,
            "height": height,
            "grid_type": "square",
            "cell_size_pixels": 100, # standard
            "terrain_layer": scenario.terrain_map
        },
        "tokens": []
    }
    
    # Export tokens from the *first* frame (initial setup)
    if scenario.frames:
        first_frame = scenario.frames[0]
        for unit in first_frame.unit_positions:
            token = {
                "name": f"{unit.side.value} - {unit.type}",
                "id": unit.unit_id,
                "x": unit.x,
                "y": unit.y,
                "side": unit.side,
                "stats": {
                    "hp": unit.health,
                    "range": unit.range,
                    "status": unit.status
                },
                "icon": config.UNIT_ICONS.get(unit.type.lower(), config.UNIT_ICONS["default"])
            }
            vtt_data["tokens"].append(token)
            
    return json.dumps(vtt_data, indent=2)

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
    
    # Attrition Report
    lines.append("## Attrition Report")
    if scenario_data.frames:
        first_frame = scenario_data.frames[0]
        last_frame = scenario_data.frames[-1]
        
        def count_units(frame):
            b, r = 0, 0
            if frame.unit_positions:
                for u in frame.unit_positions:
                    if u.side == config.UnitSide.BLUE: b += 1
                    else: r += 1
            return b, r

        b_start, r_start = count_units(first_frame)
        b_end, r_end = count_units(last_frame)
        
        lines.append(f"- **Blue Force:** Start {b_start} -> End {b_end} (Losses: {b_start - b_end})")
        lines.append(f"- **Red Force:** Start {r_start} -> End {r_end} (Losses: {r_start - r_end})")

    return "\n".join(lines)

def generate_pdf_report(scenario_data):
    """
    Generates a PDF report using FPDF.
    Returns:
        bytes: The PDF content.
    """
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    if not scenario_data or not scenario_data.frames:
        pdf.cell(0, 10, "No data available.", ln=True)
        return bytes(pdf.output())

    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Tactical Summary", ln=True)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, f"Total Frames: {len(scenario_data.frames)}", ln=True)
    pdf.ln(5)
    
    for i, frame in enumerate(scenario_data.frames):
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, f"Frame {i + 1}", ln=True)
        
        pdf.set_font("Helvetica", size=11)
        # MultiCell for description to handle wrapping
        # Use latin-1 compatible replacement for common issues if needed, 
        # strictly speaking fpdf2 core fonts are latin-1.
        desc = frame.frame_description.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, f"Situation: {desc}")
        pdf.ln(2)
        
        if hasattr(frame, 'unit_positions') and frame.unit_positions:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 8, "Unit Dispositions:", ln=True)
            
            # Simple list view for PDF instead of complex table grid for now
            pdf.set_font("Courier", size=9) # Monospace for alignment
            for unit in frame.unit_positions:
                pos_str = f"({unit.x}, {unit.y})"
                # Align columns manually with padding
                line_str = f"{unit.unit_id:<15} | {str(unit.side):<10} | {pos_str}"
                pdf.cell(0, 5, line_str, ln=True)
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Horizontal line
        pdf.ln(5)

    # Attrition Report
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Attrition Report", ln=True)
    pdf.set_font("Helvetica", size=12)
    
    if scenario_data.frames:
        first_frame = scenario_data.frames[0]
        last_frame = scenario_data.frames[-1]
        
        def count_units(frame):
            b, r = 0, 0
            if frame.unit_positions:
                for u in frame.unit_positions:
                    if u.side == config.UnitSide.BLUE: b += 1
                    else: r += 1
            return b, r

        b_start, r_start = count_units(first_frame)
        b_end, r_end = count_units(last_frame)
        
        pdf.cell(0, 10, f"Blue Force: Start {b_start} -> End {b_end} (Losses: {b_start - b_end})", ln=True)
        pdf.cell(0, 10, f"Red Force: Start {r_start} -> End {r_end} (Losses: {r_start - r_end})", ln=True)

    return bytes(pdf.output())
