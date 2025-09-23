import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from src.ocr_processor import _is_location_line

def test_is_location_line_true():
    assert _is_location_line("Conference Room 3")
    assert _is_location_line("Room 204")
    assert _is_location_line("Suite 100")
    assert _is_location_line("A1234")
    assert _is_location_line("Building 5")

def test_is_location_line_false():
    assert not _is_location_line("Daily check-in")
    assert not _is_location_line("Discuss blockers")
    assert not _is_location_line("Project discussion")
    assert not _is_location_line("")
    assert not _is_location_line("This is a long description that should not be a location.")
