"""Unit tests for Dashboard Streamlit application rendering (Module 14)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aegis.dashboard.app import render_dashboard
from aegis.services.dashboard_data import DashboardDataService


def test_render_dashboard_runs_without_exceptions() -> None:
    """Test that render_dashboard runs all tab rendering logic with mocked streamlit."""
    mock_st = MagicMock()
    # Mock tabs to return 7 context managers
    mock_tabs = [MagicMock() for _ in range(7)]
    for tab in mock_tabs:
        tab.__enter__.return_value = tab
        tab.__exit__.return_value = None
    mock_st.tabs.return_value = mock_tabs

    # Mock columns
    mock_cols = [MagicMock() for _ in range(6)]
    mock_st.columns.return_value = mock_cols

    with patch("aegis.dashboard.app.st", mock_st):
        service = DashboardDataService()
        render_dashboard(service=service)

        # Verify header and title were called
        mock_st.title.assert_called_once()
        mock_st.tabs.assert_called_once()
        assert len(mock_st.tabs.call_args[0][0]) == 7


def test_render_dashboard_empty_failures() -> None:
    """Test dashboard rendering when there are zero failed tests."""
    mock_st = MagicMock()
    mock_tabs = [MagicMock() for _ in range(7)]
    for tab in mock_tabs:
        tab.__enter__.return_value = tab
        tab.__exit__.return_value = None
    mock_st.tabs.return_value = mock_tabs
    mock_st.columns.return_value = [MagicMock() for _ in range(6)]

    service = DashboardDataService()
    # Override get_failed_tests to return empty list
    service.get_failed_tests = lambda: []  # type: ignore[method-assign]

    with patch("aegis.dashboard.app.st", mock_st):
        render_dashboard(service=service)
        # Verify success message displayed
        mock_st.success.assert_called_once()
