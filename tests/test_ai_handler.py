import pytest
from unittest.mock import MagicMock, patch
from engine.ai_handler import fetch_scenario, WargameScenario
from openai import AuthenticationError

@patch('openai.Client')
def test_fetch_scenario_success(mock_client_class, sample_scenario):
    # Setup mock
    mock_client = mock_client_class.return_value
    mock_completion = MagicMock()
    mock_completion.choices[0].message.parsed = sample_scenario
    mock_client.beta.chat.completions.parse.return_value = mock_completion
    
    # Run
    result = fetch_scenario("fake_key", "Test Context")
    
    # Verify
    assert result == sample_scenario
    mock_client.beta.chat.completions.parse.assert_called_once()

@patch('openai.Client')
def test_fetch_scenario_auth_error(mock_client_class):
    # Setup mock to raise error
    mock_client = mock_client_class.return_value
    mock_client.beta.chat.completions.parse.side_effect = AuthenticationError(message="Auth failed", response=MagicMock(), body=None)
    
    # Run & Verify
    with pytest.raises(ValueError) as excinfo:
        fetch_scenario("fake_key", "Test Context")
    assert "Invalid OpenAI API Key" in str(excinfo.value)

def test_fetch_scenario_no_key():
    with pytest.raises(ValueError) as excinfo:
        fetch_scenario("", "Test Context")
    assert "OpenAI API Key is missing" in str(excinfo.value)
