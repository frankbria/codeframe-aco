"""Unit tests for StoredDecision and MemoryLayer."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from vector_memory.coordinate import VectorCoordinate
from vector_memory.exceptions import ImmutableLayerError
from vector_memory.storage import MemoryLayer, StoredDecision


class TestStoredDecisionSerialization:
    """Test StoredDecision serialization and deserialization."""

    def test_to_json(self, mock_issue_id):
        """Test conversion to JSON dict."""
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        timestamp = datetime(2025, 1, 6, 15, 30, 0)
        decision = StoredDecision(
            coordinate=coord,
            content="Use PostgreSQL",
            timestamp=timestamp,
            agent_id="claude-code-01",
            issue_context={"issue_id": "test-123"},
        )

        json_data = decision.to_json()

        assert json_data["coordinate"]["x"] == mock_issue_id(5)
        assert json_data["coordinate"]["y"] == 2
        assert json_data["coordinate"]["z"] == 1
        assert json_data["content"] == "Use PostgreSQL"
        assert json_data["agent_id"] == "claude-code-01"
        assert json_data["issue_context"]["issue_id"] == "test-123"

    def test_from_json(self, mock_issue_id):
        """Test deserialization from JSON dict."""
        json_data = {
            "coordinate": {"x": mock_issue_id(5), "y": 2, "z": 1},
            "content": "Use PostgreSQL",
            "timestamp": "2025-01-06T15:30:00",
            "agent_id": "claude-code-01",
            "issue_context": {"issue_id": "test-123"},
        }

        decision = StoredDecision.from_json(json_data)

        assert decision.coordinate.x == mock_issue_id(5)
        assert decision.content == "Use PostgreSQL"
        assert decision.agent_id == "claude-code-01"
        assert decision.issue_context["issue_id"] == "test-123"

    def test_json_roundtrip(self, mock_issue_id):
        """Test JSON serialization roundtrip."""
        coord = VectorCoordinate(x=mock_issue_id(42), y=3, z=2)
        timestamp = datetime.now()
        original = StoredDecision(
            coordinate=coord,
            content="Test decision",
            timestamp=timestamp,
            agent_id="test-agent",
            issue_context=None,
        )

        json_data = original.to_json()
        recovered = StoredDecision.from_json(json_data)

        assert recovered.coordinate == original.coordinate
        assert recovered.content == original.content
        assert recovered.agent_id == original.agent_id
        # Timestamp comparison (may lose microsecond precision in ISO format)
        assert abs((recovered.timestamp - original.timestamp).total_seconds()) < 1

    def test_to_file_and_from_file(self, mock_issue_id):
        """Test file I/O operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
            original = StoredDecision(
                coordinate=coord,
                content="Test content",
                timestamp=datetime.now(),
                agent_id="test-agent",
            )

            # Write to file
            file_path = tmpdir_path / "test-decision.json"
            original.to_file(file_path)

            # Verify file exists and is valid JSON
            assert file_path.exists()
            with open(file_path) as f:
                json_content = json.load(f)
            assert json_content["content"] == "Test content"

            # Read from file
            recovered = StoredDecision.from_file(file_path)
            assert recovered.content == original.content
            assert recovered.coordinate == original.coordinate

    def test_to_file_creates_directory(self, mock_issue_id):
        """Test that to_file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
            decision = StoredDecision(
                coordinate=coord,
                content="Test",
                timestamp=datetime.now(),
                agent_id="test",
            )

            # Write to nested path that doesn't exist
            nested_path = tmpdir_path / "level1" / "level2" / "decision.json"
            decision.to_file(nested_path)

            assert nested_path.exists()
            assert nested_path.parent.exists()


class TestMemoryLayer:
    """Test MemoryLayer functionality."""

    def test_layer_constants(self):
        """Test predefined layer constants."""
        assert MemoryLayer.ARCHITECTURE.z == 1
        assert MemoryLayer.ARCHITECTURE.is_immutable is True

        assert MemoryLayer.INTERFACES.z == 2
        assert MemoryLayer.INTERFACES.is_immutable is False

        assert MemoryLayer.IMPLEMENTATION.z == 3
        assert MemoryLayer.IMPLEMENTATION.is_immutable is False

        assert MemoryLayer.EPHEMERAL.z == 4
        assert MemoryLayer.EPHEMERAL.is_immutable is False

    def test_get_layer(self):
        """Test retrieving layer by z value."""
        layer1 = MemoryLayer.get_layer(1)
        assert layer1.name == "Architecture"
        assert layer1.is_immutable is True

        layer2 = MemoryLayer.get_layer(2)
        assert layer2.name == "Interfaces"

    def test_get_layer_invalid(self):
        """Test retrieving invalid layer."""
        with pytest.raises(ValueError, match="Invalid layer"):
            MemoryLayer.get_layer(5)

    def test_validate_write_immutable_empty(self, mock_issue_id):
        """Test writing to empty immutable layer (allowed)."""
        layer = MemoryLayer.ARCHITECTURE
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)

        # Should not raise - writing to empty coordinate is allowed
        layer.validate_write(coord, existing_decision=None)

    def test_validate_write_immutable_occupied(self, mock_issue_id):
        """Test writing to occupied immutable layer (not allowed)."""
        layer = MemoryLayer.ARCHITECTURE
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=1)
        existing = StoredDecision(
            coordinate=coord,
            content="Existing",
            timestamp=datetime.now(),
            agent_id="test",
        )

        with pytest.raises(ImmutableLayerError, match="Cannot modify decision"):
            layer.validate_write(coord, existing_decision=existing)

    def test_validate_write_mutable_occupied(self, mock_issue_id):
        """Test writing to occupied mutable layer (allowed)."""
        layer = MemoryLayer.IMPLEMENTATION
        coord = VectorCoordinate(x=mock_issue_id(5), y=3, z=3)
        existing = StoredDecision(
            coordinate=coord,
            content="Existing",
            timestamp=datetime.now(),
            agent_id="test",
        )

        # Should not raise - mutable layers can be overwritten
        layer.validate_write(coord, existing_decision=existing)

    def test_validate_delete(self, mock_issue_id):
        """Test that deletion is not supported."""
        layer = MemoryLayer.EPHEMERAL
        coord = VectorCoordinate(x=mock_issue_id(5), y=2, z=4)

        with pytest.raises(ImmutableLayerError, match="Cannot delete"):
            layer.validate_delete(coord)
