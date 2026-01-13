import pytest
import utils.exporter as exporter
from engine.ai_handler import WargameScenario

def test_generate_markdown_report_valid(sample_scenario):
    report = exporter.generate_markdown_report(sample_scenario)
    
    assert "# Commander's Journal" in report
    assert "**Total Frames:** 2" in report
    assert "### Frame 1" in report
    assert "Start" in report
    assert "A1" in report
    assert "B1" in report

def test_generate_markdown_report_empty():
    empty_scenario = WargameScenario(terrain_map=[], frames=[])
    report = exporter.generate_markdown_report(empty_scenario)
    assert "No data available" in report
    
    none_report = exporter.generate_markdown_report(None)
    assert "No data available" in none_report
