"""Tests for openpauw.board (no hardware required)."""

from openpauw.board import parse_state


class TestParseState:
    def test_valid_state(self):
        line = "STATE CFG=1 IP=A IM=B VP=C VM=D"
        result = parse_state(line)
        assert result is not None
        assert result["cfg"] == "1"
        assert result["ip"] == "A"
        assert result["im"] == "B"
        assert result["vp"] == "C"
        assert result["vm"] == "D"

    def test_custom_config(self):
        line = "STATE CFG=0 IP=A IM=D VP=C VM=B"
        result = parse_state(line)
        assert result is not None
        assert result["cfg"] == "0"
        assert result["ip"] == "A"
        assert result["vm"] == "B"

    def test_not_state_line(self):
        assert parse_state("OK CFG 1") is None

    def test_missing_cfg(self):
        assert parse_state("STATE IP=A IM=B") is None

    def test_empty(self):
        assert parse_state("") is None
