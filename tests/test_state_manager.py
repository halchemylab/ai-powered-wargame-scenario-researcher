import pytest
from unittest.mock import MagicMock, patch
import utils.state_manager as state_manager

# Mock class that behaves like Streamlit's session state (dict + attribute access)
class MockSessionState(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'MockSessionState' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

@pytest.fixture
def mock_session_state():
    # We replace st.session_state with our custom mock
    mock_state = MockSessionState()
    with patch('streamlit.session_state', mock_state):
        yield mock_state

def test_initialize_state(mock_session_state):
    state_manager.initialize_state()
    assert 'total_frames_generated' in mock_session_state
    assert 'total_scenarios_run' in mock_session_state
    assert 'current_scenario' in mock_session_state
    assert 'current_frame_index' in mock_session_state

def test_set_scenario(mock_session_state, sample_scenario):
    state_manager.initialize_state()
    state_manager.set_scenario(sample_scenario)
    
    assert mock_session_state['current_scenario'] == sample_scenario
    assert mock_session_state['current_frame_index'] == 0
    assert mock_session_state['total_scenarios_run'] == 1
    assert mock_session_state['total_frames_generated'] == 2

def test_navigation(mock_session_state, sample_scenario):
    state_manager.initialize_state()
    state_manager.set_scenario(sample_scenario)
    
    # Check initial
    assert mock_session_state['current_frame_index'] == 0
    
    # Next frame
    state_manager.next_frame()
    assert mock_session_state['current_frame_index'] == 1
    
    # Next frame (should stay at max)
    state_manager.next_frame()
    assert mock_session_state['current_frame_index'] == 1
    
    # Prev frame
    state_manager.prev_frame()
    assert mock_session_state['current_frame_index'] == 0
    
    # Prev frame (should stay at 0)
    state_manager.prev_frame()
    assert mock_session_state['current_frame_index'] == 0
