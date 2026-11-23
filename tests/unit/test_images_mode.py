"""Parse-only --images mode: range-verified extraction and range-scoped CalDAV sync."""
import json
import sys
from datetime import date, datetime, timezone

import pytest
from icalendar import Calendar, Event

import src.sync_tool as sync_tool
from src.models.calendar_data import ParsedEvent, WeekExtraction
from src.sync_tool import sync_from_images

NOW = datetime(2026, 11, 24, 15, 0, tzinfo=timezone.utc)   # Tue 2026-11-24 10:00 ET
W0 = (date(2026, 11, 23), date(2026, 11, 27))
W1 = (date(2026, 11, 30), date(2026, 12, 4))


def ev(day, title="Standup", start="12:15", end="12:30"):
    return ParsedEvent(start_datetime=f"{day}T{start}:00", end_datetime=f"{day}T{end}:00", title=title)


def ics(uid, start_utc, end_utc):
    cal = Calendar()
    e = Event()
    e.add("uid", uid)
    e.add("summary", "x")
    e.add("dtstart", start_utc)
    e.add("dtend", end_utc)
    cal.add_component(e)
    return cal.to_ical().decode()


class FakeObj:
    def __init__(self, data):
        self.data = data


class FakeClient:
    instances = []

    def __init__(self, url, user, pw, verify=True, existing=None):
        self.existing = dict(existing or {})
        self.deleted, self.put = [], []
        FakeClient.instances.append(self)

    def get_events(self):
        return {u: FakeObj(d) for u, d in self.existing.items()}

    def delete_event(self, url):
        self.deleted.append(url)
        return True

    def put_event(self, uid, data):
        self.put.append(uid)
        return True


def factory(existing=None):
    FakeClient.instances = []
    return lambda *a, **k: FakeClient(*a, existing=existing, **k)


def fake_extractor(results):
    calls = iter(results)

    def _ex(path, **kw):
        r = next(calls)
        if isinstance(r, Exception):
            raise r
        return r
    return _ex


@pytest.fixture
def cfg(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"caldav_url": "https://cal/x/", "caldav_username": "u",
                             "caldav_password": "p", "outlook_calendar_name": "Calendar",
                             "use_bedrock_vision": True}))
    return str(p)


def run(cfg, tmp_path, results, existing=None, images=("w0.png", "w1.png")):
    return sync_from_images(cfg, list(images), extractor=fake_extractor(results),
                            client_factory=factory(existing), now=NOW,
                            archive_dir=str(tmp_path / "arch"))


def test_images_mode_syncs_two_weeks(cfg, tmp_path):
    r = run(cfg, tmp_path, [
        WeekExtraction(*W0, [ev("2026-11-24"), ev("2026-11-25"), ev("2026-11-26")]),
        WeekExtraction(*W1, [ev("2026-12-01"), ev("2026-12-02")]),
    ])
    assert r["ok"] is True
    assert r["created"] == 5
    assert r["per_image"] == [3, 2]
    assert r["ranges"] == [["2026-11-23", "2026-11-27"], ["2026-11-30", "2026-12-04"]]
    assert len(FakeClient.instances[0].put) == 5


def test_deletion_scoped_to_ranges(cfg, tmp_path):
    existing = {
        "u/a.ics": ics("a", datetime(2026, 11, 25, 17, 15, tzinfo=timezone.utc), datetime(2026, 11, 25, 17, 30, tzinfo=timezone.utc)),
        "u/b.ics": ics("b", datetime(2026, 12, 2, 17, 15, tzinfo=timezone.utc), datetime(2026, 12, 2, 17, 30, tzinfo=timezone.utc)),
        "u/c.ics": ics("c", datetime(2026, 12, 15, 17, 15, tzinfo=timezone.utc), datetime(2026, 12, 15, 17, 30, tzinfo=timezone.utc)),
    }
    r = run(cfg, tmp_path, [WeekExtraction(*W0, [ev("2026-11-25")]), WeekExtraction(*W1, [ev("2026-12-02")])], existing)
    assert r["ok"] is True
    assert sorted(FakeClient.instances[0].deleted) == ["u/a.ics", "u/b.ics"]
    assert r["deleted"] == 2


def test_past_events_in_range_not_deleted(cfg, tmp_path):
    existing = {"u/past.ics": ics("p", datetime(2026, 11, 23, 17, 15, tzinfo=timezone.utc), datetime(2026, 11, 23, 17, 30, tzinfo=timezone.utc))}
    r = run(cfg, tmp_path, [WeekExtraction(*W0, [ev("2026-11-25")]), WeekExtraction(*W1, [])], existing)
    assert r["ok"] is True
    assert FakeClient.instances[0].deleted == []


def test_images_mode_aborts_when_range_unreadable(cfg, tmp_path):
    existing = {"u/a.ics": ics("a", datetime(2026, 11, 25, 17, 15, tzinfo=timezone.utc), datetime(2026, 11, 25, 17, 30, tzinfo=timezone.utc))}
    r = run(cfg, tmp_path, [WeekExtraction(*W0, [ev("2026-11-25")]), WeekExtraction(None, None, [])], existing)
    assert r["ok"] is False
    assert "week 1" in r["error"]
    c = FakeClient.instances[0] if FakeClient.instances else None
    assert c is None or (c.deleted == [] and c.put == [])


def test_empty_week_with_proven_range_ok(cfg, tmp_path):
    existing = {"u/stale.ics": ics("s", datetime(2026, 11, 26, 17, 15, tzinfo=timezone.utc), datetime(2026, 11, 26, 17, 30, tzinfo=timezone.utc))}
    r = run(cfg, tmp_path, [WeekExtraction(*W0, []), WeekExtraction(*W1, [ev("2026-12-01"), ev("2026-12-03")])], existing)
    assert r["ok"] is True
    assert r["per_image"] == [0, 2]
    assert FakeClient.instances[0].deleted == ["u/stale.ics"]


def test_out_of_range_events_dropped(cfg, tmp_path):
    r = run(cfg, tmp_path, [WeekExtraction(*W0, [ev("2026-11-24"), ev("2026-12-09")]), WeekExtraction(*W1, [ev("2026-12-01")])])
    assert r["ok"] is True
    assert r["per_image"] == [1, 1]
    assert r["created"] == 2


def test_ocr_fallback_disabled(cfg, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("OCR fallback must not run in --images mode")
    monkeypatch.setattr(sync_tool, "process_image_with_ocr", boom)
    r = run(cfg, tmp_path, [RuntimeError("bedrock down"), WeekExtraction(*W1, [])])
    assert r["ok"] is False
    assert "bedrock down" in r["error"]
    c = FakeClient.instances[0] if FakeClient.instances else None
    assert c is None or (c.deleted == [] and c.put == [])


def test_json_result_written_on_exception(tmp_path, monkeypatch):
    import sync_outlook_caldav
    out = tmp_path / "r.json"
    monkeypatch.setattr(sys, "argv", ["x", "--config", str(tmp_path / "missing.json"),
                                      "--images", "a.png", "b.png", "--json-result", str(out)])
    with pytest.raises(SystemExit) as e:
        sync_outlook_caldav.main()
    assert e.value.code == 1
    d = json.loads(out.read_text())
    assert d["ok"] is False and d["error"]


def test_past_parsed_events_not_recreated(cfg, tmp_path):
    # NOW = Tue 2026-11-24 10:00 ET. Monday's standup ended; it was kept (not deleted), so it
    # must not be created again either, or every run adds a duplicate of each past event.
    r = run(cfg, tmp_path, [
        WeekExtraction(*W0, [ev("2026-11-23"), ev("2026-11-24", start="09:00", end="09:30"),
                             ev("2026-11-24", start="12:15", end="12:30")]),
        WeekExtraction(*W1, [ev("2026-12-01")]),
    ])
    assert r["ok"] is True
    assert r["created"] == 2          # Tue 12:15 + Dec 1; Mon and Tue 09:00 already ended
    assert r["per_image"] == [3, 1]   # still counts what Outlook shows
