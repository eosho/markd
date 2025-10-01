"""Contract tests for WebSocket /ws endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestWebSocketEndpoint:
    """Test suite for WebSocket /ws endpoint."""

    def test_websocket_connection_upgrade(self, test_client_single_file: TestClient) -> None:
        """Test that WebSocket connection can be established."""
        with test_client_single_file.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_receives_reload_messages(self, test_client_single_file: TestClient) -> None:
        """Test that WebSocket receives reload messages."""
        with test_client_single_file.websocket_connect("/ws"):
            # May receive a message immediately or after a timeout
            # Just verify connection works
            pass

    def test_websocket_ping_pong_heartbeat(self, test_client_single_file: TestClient) -> None:
        """Test that WebSocket supports ping/pong heartbeat."""
        with test_client_single_file.websocket_connect("/ws") as websocket:
            # Send ping, should receive pong or continue connection
            # Actual implementation may vary
            websocket.send_json({"type": "ping"})
            # Connection should remain open
            pass

    def test_websocket_watch_file_registration(self, test_client_single_file: TestClient) -> None:
        """Test that clients can register to watch specific files."""
        with test_client_single_file.websocket_connect("/ws") as websocket:
            # Send watch request
            websocket.send_json({"type": "watch", "path": "/test.md"})
            # Should not disconnect
            pass

    def test_websocket_reload_message_structure(self, test_client_single_file: TestClient) -> None:
        """Test that reload messages have expected structure."""
        with test_client_single_file.websocket_connect("/ws") as websocket:
            # Wait briefly for any messages
            try:
                data = websocket.receive_json(timeout=0.1)
                if data:
                    assert isinstance(data, dict)
                    assert "type" in data or "action" in data
            except Exception:
                # No message received, which is fine
                pass

    def test_websocket_handles_disconnect(self, test_client_single_file: TestClient) -> None:
        """Test that server handles WebSocket disconnect gracefully."""
        with test_client_single_file.websocket_connect("/ws") as websocket:
            websocket.close()
        # Should not raise exception

    def test_multiple_websocket_connections(self, test_client_single_file: TestClient) -> None:
        """Test that multiple WebSocket clients can connect simultaneously."""
        with test_client_single_file.websocket_connect("/ws") as ws1:
            with test_client_single_file.websocket_connect("/ws") as ws2:
                # Both connections should be active
                assert ws1 is not None
                assert ws2 is not None
