import json
import os
import tempfile

import Feed as Feed_mod
import request as request_mod
from Feed import Feed, current_unix_time
from PickleDictionary import PickleDictionary

TEST_FILES = []


def teardown_module(module):
    # Clean up temporary test pickle files
    for test_file in TEST_FILES:
        file_path = f"pickles/{test_file}"
        if os.path.exists(file_path):
            os.remove(file_path)


def _get_temp_filename():
    """Generate a unique temporary filename for test pickles"""
    os.makedirs("pickles", exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=".dat", dir="pickles", prefix="test_")
    os.close(fd)
    os.remove(temp_path)  # Remove the file, just use the name
    filename = os.path.basename(temp_path)
    TEST_FILES.append(filename)
    return filename


class DummyResponse:
    def __init__(self, text: str):
        self.text = text
        self.status_code = 200

        class Req:
            def __init__(self):
                self.path_url = "/"

        self.request = Req()


def test_instagram_profile_entries(monkeypatch):
    now = current_unix_time()
    profile_data = {
        "graphql": {
            "user": {
                "edge_owner_to_timeline_media": {
                    "edges": [
                        {
                            "node": {
                                "shortcode": "abc123",
                                "taken_at_timestamp": now - 120,
                                "edge_media_to_caption": {
                                    "edges": [{"node": {"text": "First caption"}}]
                                },
                            }
                        },
                        {
                            "node": {
                                "shortcode": "def456",
                                "taken_at_timestamp": now - 60,
                                "edge_media_to_caption": {"edges": []},
                            }
                        },
                    ]
                }
            }
        }
    }

    def fake_request(url, headers=None, cookies=None):
        return DummyResponse(json.dumps(profile_data))

    monkeypatch.setattr(request_mod, "request", fake_request)
    monkeypatch.setattr(Feed_mod, "request", fake_request)

    feed_item = {"url": "https://www.instagram.com/example"}
    rss_urls = PickleDictionary(_get_temp_filename())
    last_times = PickleDictionary(_get_temp_filename())
    monthly = PickleDictionary(_get_temp_filename())

    rss_urls[feed_item["url"]] = feed_item["url"]
    last_times[feed_item["url"]] = 0

    feed = Feed(feed_item, rss_urls, last_times, monthly, wrappers={})

    class SimpleQueue:
        def __init__(self):
            self._queue = []

        def enqueue(self, entry):
            self._queue.append(entry)

    sq = SimpleQueue()
    feed.process_feed(sq)

    assert len(sq._queue) == 2
    urls = [entry.url for entry in sq._queue]
    assert "https://www.instagram.com/p/abc123/" in urls
    assert "https://www.instagram.com/p/def456/" in urls
    assert monthly[feed_item["url"]] == 2
    newest_publish_time = max(entry.publish_time for entry in sq._queue)
    assert last_times[feed_item["url"]] == newest_publish_time
