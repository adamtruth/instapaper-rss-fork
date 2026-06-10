import pytest
from bs4 import BeautifulSoup

import SavingQueue as SavingQueue_mod
from SavingQueue import SavingQueue
from Entry import Entry


def _make_entry(url="https://example.com/1", folder=None):
    xml = f"<item><title>Test</title><link>{url}</link><pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate></item>"
    tag = BeautifulSoup(xml, features="xml").find("item")
    return Entry(tag, folder=folder)


def _make_queue(monkeypatch, testing_mode=True, folders=None):
    """Create a SavingQueue bypassing all network and file I/O."""
    monkeypatch.setattr(SavingQueue, "_get_cookies", lambda self: setattr(self, "_cookies", {}))
    monkeypatch.setattr(SavingQueue, "_get_form_key", lambda self: setattr(self, "_form_key", "testkey"))
    monkeypatch.setattr(SavingQueue, "_load_folders", lambda self: setattr(self, "_folders", folders or {}))
    return SavingQueue(testing_mode=testing_mode)


# Testing mode output
def test_testing_mode_no_folder(monkeypatch, capsys):
    sq = _make_queue(monkeypatch)
    sq.enqueue(_make_entry("https://example.com/1"))
    sq.save_entries()
    assert "Would have saved https://example.com/1" in capsys.readouterr().out


def test_testing_mode_with_folder(monkeypatch, capsys):
    sq = _make_queue(monkeypatch, folders={"Tech": "42"})
    sq.enqueue(_make_entry("https://example.com/1", folder="Tech"))
    sq.save_entries()
    out = capsys.readouterr().out
    assert "only to folder 'Tech'" in out


# Folder config validation
def test_get_folder_id_raises_for_unknown_folder(monkeypatch):
    sq = _make_queue(monkeypatch, folders={"Tech": "42"})
    with pytest.raises(ValueError, match="not defined in config/folders.yml"):
        sq._get_folder_id("Nonexistent")


def test_get_folder_id_returns_correct_id(monkeypatch):
    sq = _make_queue(monkeypatch, folders={"Tech": "42", "News": "99"})
    assert sq._get_folder_id("Tech") == "42"
    assert sq._get_folder_id("News") == "99"


# Live save behaviour (non-testing mode)
class DummyResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.url = ""


def test_save_no_folder_calls_instapaper_once(monkeypatch):
    calls = []

    def fake_request(url, cookies=None):
        calls.append(url)
        return DummyResponse(text='<a href="/read/99">title</a>')

    monkeypatch.setattr(SavingQueue_mod, "request", fake_request)
    sq = _make_queue(monkeypatch, testing_mode=False)
    sq.enqueue(_make_entry("https://example.com/1"))
    sq.save_entries()

    assert len(calls) == 1
    assert "instapaper.com/add" in calls[0]


def test_save_with_folder_saves_then_moves(monkeypatch):
    calls = []

    def fake_request(url, cookies=None):
        calls.append(url)
        return DummyResponse(text='<a href="/read/77">title</a>')

    monkeypatch.setattr(SavingQueue_mod, "request", fake_request)
    sq = _make_queue(monkeypatch, testing_mode=False, folders={"Tech": "42"})
    sq.enqueue(_make_entry("https://example.com/1", folder="Tech"))
    sq.save_entries()

    assert len(calls) == 2
    assert "instapaper.com/add" in calls[0]
    assert "instapaper.com/move/77/to/42" in calls[1]


def test_move_to_folder_raises_on_404(monkeypatch):
    def fake_request(url, cookies=None):
        if "move" in url:
            return DummyResponse(status_code=404)
        return DummyResponse(text='<a href="/read/77">title</a>')

    monkeypatch.setattr(SavingQueue_mod, "request", fake_request)
    sq = _make_queue(monkeypatch, testing_mode=False, folders={"Tech": "42"})
    sq.enqueue(_make_entry("https://example.com/1", folder="Tech"))

    with pytest.raises(ValueError, match="404"):
        sq.save_entries()
