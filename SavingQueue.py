import os
import re
import urllib.parse
from typing import List

import yaml
from rich.progress import track

from Entry import Entry
from request import request

COOKIE_PROBLEM_PAGE_URL = "https://www.instapaper.com/hello2?u=https%3A%2F%2Fexample.com&s=&cookie_notice=1&a=%20read-later"


class SavingQueue:
    def __init__(self, testing_mode: bool) -> None:
        self._entries: List[Entry] = []
        self._testing_mode = testing_mode
        if not testing_mode:
            self._get_cookies()
            self._get_form_key()
        self._load_folders()

    def enqueue(self, entry: Entry) -> None:
        self._entries.append(entry)

    def __len__(self) -> int:
        return len(self._entries)

    def _sort_entries(self) -> None:
        self._entries = sorted(self._entries, key=(lambda entry: entry.url))

    def _get_cookies(self) -> None:
        # Load cookies from YAML file
        cookie_path = "config/cookies.yml"
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(
                "No cookies file found at config/cookies.yml. "
                "Create config/cookies.yml with your cookie mapping (pfh, pfp, pfu)."
            )

        with open(cookie_path, "r") as f:
            cookies = yaml.safe_load(f) or {}

        if not isinstance(cookies, dict):
            raise ValueError(
                "config/cookies.yml must contain a mapping of cookie names to values"
            )

        self._cookies = cookies

    def _get_form_key(self) -> None:
        cookie_problem_page = request(
            COOKIE_PROBLEM_PAGE_URL, cookies=self._cookies
        ).text
        start_match = re.search(
            '<input type="hidden" name="form_key" value="', cookie_problem_page
        )
        if start_match is None:
            raise ValueError(
                "Could not find Instapaper form key. "
                "Your cookies in config/cookies.yml may be missing or expired."
            )
        start_index = start_match.end()
        end_index = (
            re.search('"/>', cookie_problem_page[start_index:]).start() + start_index
        )
        self._form_key = cookie_problem_page[start_index:end_index]

    def _load_folders(self) -> None:
        folder_path = "config/folders.yml"
        if not os.path.exists(folder_path):
            self._folders: dict[str, str] = {}
            return

        with open(folder_path, "r") as f:
            data = yaml.safe_load(f) or {}

        folders_list = data.get("folders") or []
        self._folders = {
            item["folder_name"]: str(item["folder_id"])
            for item in folders_list
            if item.get("folder_name") and item.get("folder_id") is not None
        }

    def _get_folder_id(self, folder_name: str) -> str:
        if folder_name not in self._folders:
            raise ValueError(
                f"Folder '{folder_name}' is not defined in config/folders.yml"
            )
        return self._folders[folder_name]

    def _save_to_instapaper(self, url: str) -> str:
        """Save a URL to Instapaper and return the article_id from the redirect URL."""
        instapaper_url = f"https://www.instapaper.com/add?url={urllib.parse.quote(url)}&form_key={self._form_key}"
        response = request(instapaper_url, cookies=self._cookies)

        if response.status_code // 100 != 2:
            print(f"Instapaper save link failed: {url}")
            return ""

        match = re.search(r"/read/(\d+)", response.text)
        if not match:
            print(f"Could not parse article_id from Instapaper response for: {url}")
            return ""

        return match.group(1)

    def _move_to_folder(self, article_id: str, folder_id: str, folder_name: str, url: str) -> None:
        """Move an article to a folder. Raises ValueError on 404."""
        move_url = f"https://www.instapaper.com/move/{article_id}/to/{folder_id}"
        response = request(move_url, cookies=self._cookies)

        if response.status_code == 404:
            raise ValueError(
                f"Folder '{folder_name}' (id: {folder_id}) not found on Instapaper (404). "
                "Check that the folder_id in config/folders.yml is correct."
            )
        elif response.status_code // 100 != 2:
            print(f"Instapaper folder move failed: {url} to folder '{folder_name}'")

    def save_entries(self) -> None:
        self._sort_entries()

        for entry in track(self._entries, description="[bold green]Saving entries..."):
            if self._testing_mode:
                if entry.folder:
                    print(f"Would have saved {entry.url} only to folder '{entry.folder}'")
                else:
                    print(f"Would have saved {entry.url}")
                continue

            if entry.folder:
                folder_id = self._get_folder_id(entry.folder)
                article_id = self._save_to_instapaper(entry.url)
                if article_id:
                    self._move_to_folder(article_id, folder_id, entry.folder, entry.url)
            else:
                self._save_to_instapaper(entry.url)
