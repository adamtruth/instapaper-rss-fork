from datetime import datetime, timezone
from time import mktime

from bs4 import Tag
from dateutil.parser import parse as rfc2822_parse

from PickleDictionary import PickleDictionary


def current_unix_time() -> int:
    date_time = datetime.now(timezone.utc)
    return int(mktime(date_time.timetuple()))


def date_string_to_unix_timestamp(date_string: str) -> int:
    try:
        date_time = datetime.fromisoformat(date_string)  # ATOM (RFC 3339)
    except ValueError:
        date_time = rfc2822_parse(date_string)  # RSS (RFC 2822)

    return int(mktime(date_time.timetuple()))


class Entry:
    def __init__(
        self,
        entry_tag: Tag,
        wrappers: list[str] | None = None,
        folder: str | None = None,
    ) -> None:
        self._entry_tag = entry_tag
        self._wrappers = wrappers or []
        self.folder = folder

        try:
            self.title = entry_tag.find_next("title").text.strip()
        except AttributeError:
            self.title = ""

        base_url = self._get_url()
        self.url = self._apply_wrappers(base_url)
        self.publish_time = self._get_publish_time()

    def _get_publish_time(self) -> int:
        date_tag_names = [
            "pubDate",  # RSS
            "published",  # ATOM
            "updated",  # Fallback
        ]

        # Get date from entry tag child
        for date_tag_name in date_tag_names:
            date_tag = self._entry_tag.find(date_tag_name)

            if date_tag is not None:
                break

        # Return tag-derived publish time
        if date_tag is not None:
            publish_time = date_tag.text
            return date_string_to_unix_timestamp(publish_time)

        # Get publish time from cache
        pickle_dictionary = PickleDictionary("entry_dates.dat")
        try:
            unix_time = pickle_dictionary[self.url]
        except KeyError:
            unix_time = current_unix_time()
            pickle_dictionary[self.url] = unix_time
            pickle_dictionary.save()

        return unix_time

    def _get_url(self) -> str:
        # Get URL
        url = self._entry_tag.find_next("link").get("href")
        if url is None:
            url = self._entry_tag.find_next("link").text

        # Convert YouTube Shorts links to regular video links
        if url.startswith("https://www.youtube.com/shorts/"):
            url = url.replace(
                "https://www.youtube.com/shorts/", "https://www.youtube.com/watch?v="
            )

        return url

    def _apply_wrappers(self, url: str) -> str:
        final_url = url

        for wrapper_template in self._wrappers:
            if "{url}" not in wrapper_template:
                raise ValueError("Wrapper template is missing the '{url}' placeholder")

            # Insert the URL directly without URL-encoding
            final_url = wrapper_template.replace("{url}", final_url)

        return final_url
