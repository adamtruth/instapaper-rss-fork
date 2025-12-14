import pytest
from bs4 import BeautifulSoup

from Entry import Entry, date_string_to_unix_timestamp


def make_entry(xml: str, wrappers=None) -> Entry:
    soup = BeautifulSoup(xml, features="xml")
    tag = soup.find("entry") or soup.find("item")
    return Entry(tag, wrappers)


def test_entry_title_parsing():
    xml = """
    <entry>
      <title> Hello World </title>
      <link href="https://example.com/post" />
      <published>2024-01-02T03:04:05+00:00</published>
    </entry>
    """
    e = make_entry(xml)
    assert e.title == "Hello World"


def test_entry_url_shorts_conversion():
    xml = """
    <entry>
      <title>Shorts</title>
      <link href="https://www.youtube.com/shorts/abc123" />
      <published>2024-01-02T03:04:05+00:00</published>
    </entry>
    """
    e = make_entry(xml)
    assert e.url == "https://www.youtube.com/watch?v=abc123"


def test_entry_url_text_link():
    xml = """
    <item>
      <title>Text link</title>
      <link>https://example.org/path</link>
      <pubDate>Tue, 02 Jan 2024 03:04:05 +0000</pubDate>
    </item>
    """
    e = make_entry(xml)
    assert e.url == "https://example.org/path"


def test_entry_wrappers_apply_in_order():
    xml = """
    <item>
      <title>Wrap</title>
      <link>https://example.com/a</link>
      <pubDate>Tue, 02 Jan 2024 03:04:05 +0000</pubDate>
    </item>
    """
    wrappers = [
        "https://wrapper1/?u={url}",
        "https://wrapper2/?redir={url}",
    ]
    e = make_entry(xml, wrappers)
    assert e.url == "https://wrapper2/?redir=https://wrapper1/?u=https://example.com/a"


def test_wrapper_missing_placeholder_raises():
    xml = """
    <item>
      <title>Wrap</title>
      <link>https://example.com/a</link>
      <pubDate>Tue, 02 Jan 2024 03:04:05 +0000</pubDate>
    </item>
    """
    with pytest.raises(ValueError):
        make_entry(xml, ["https://bad-wrapper/"])


def test_date_string_parsing_atom_and_rss():
    atom_ts = date_string_to_unix_timestamp("2024-01-02T03:04:05+00:00")
    rss_ts = date_string_to_unix_timestamp("Tue, 02 Jan 2024 03:04:05 +0000")
    assert isinstance(atom_ts, int) and isinstance(rss_ts, int)
    # Different formats should still parse to valid (close) ints
    assert atom_ts > 0 and rss_ts > 0
