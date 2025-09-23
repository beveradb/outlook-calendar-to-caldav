import re
import pytest

def test_time_range_pattern_valid():
    pattern = re.compile(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)')
    match = pattern.search('10:00 AM - 11:00 AM Meeting with John')
    assert match
    assert match.group(1) == '10:00 AM'
    assert match.group(2) == '11:00 AM'

def test_time_range_pattern_invalid():
    pattern = re.compile(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)')
    # Should not match missing AM/PM
    assert not pattern.search('10:00 - 11:00 Meeting')
    # Should not match 24-hour format
    assert not pattern.search('14:00 - 15:00 Meeting')

def test_all_day_pattern():
    pattern = re.compile(r'All Day\s*(.*)')
    match = pattern.search('All Day Holiday')
    assert match
    assert match.group(1) == 'Holiday'
    match2 = pattern.search('All Day')
    assert match2
    assert match2.group(1) == ''
