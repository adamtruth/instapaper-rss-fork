from urllib.parse import urlparse

import yaml

VALID_KEYS = {
    "url",
    "description",
    "priority",
    "wrappers",
    "blacklist_regex",
    "whitelist_regex",
    "allowed_languages",
    "folder",
}


def is_url_valid_syntax(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def test_wrappers_yaml_is_mapping():
    with open("config/wrappers.yml", "r") as f:
        wrappers = yaml.safe_load(f)
    assert isinstance(wrappers, dict), "config/wrappers.yml must be a mapping"


def test_folders_yaml_structure():
    with open("config/folders.yml", "r") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "config/folders.yml must be a mapping"
    folders = data.get("folders", [])
    assert isinstance(folders, list), "config/folders.yml 'folders' must be a list"
    seen_names = set()
    seen_ids = set()
    for folder in folders:
        assert isinstance(folder, dict), "Each folder entry must be a mapping"
        assert "folder_name" in folder, "Each folder must have a 'folder_name'"
        assert "folder_id" in folder, "Each folder must have a 'folder_id'"
        assert isinstance(folder["folder_name"], str), "folder_name must be a string"
        name = folder["folder_name"]
        folder_id = str(folder["folder_id"])
        assert name not in seen_names, f"Duplicate folder_name: '{name}'"
        assert folder_id not in seen_ids, f"Duplicate folder_id: '{folder_id}'"
        seen_names.add(name)
        seen_ids.add(folder_id)


def test_sources_yaml_structure_and_constraints():
    with open("config/sources.yml", "r") as f:
        categories = yaml.safe_load(f)
    with open("config/wrappers.yml", "r") as f:
        wrappers = yaml.safe_load(f)
    with open("config/settings.yml", "r") as f:
        settings = yaml.safe_load(f)
    with open("config/priorities.yml", "r") as f:
        priorities = yaml.safe_load(f)
    with open("config/folders.yml", "r") as f:
        folders_data = yaml.safe_load(f) or {}
    known_folders = {
        item["folder_name"]
        for item in (folders_data.get("folders") or [])
        if isinstance(item, dict) and "folder_name" in item
    }

    assert isinstance(categories, list), "config/sources.yml must be a list"
    assert isinstance(wrappers, dict), "config/wrappers.yml must be a mapping"
    assert isinstance(settings, dict), "config/settings.yml must be a mapping"
    assert isinstance(priorities, dict), "config/priorities.yml must be a mapping"
    assert settings.get("default_priority") in priorities, (
        "default_priority in config/settings.yml must exist in config/priorities.yml"
    )

    for priority_name, rules in priorities.items():
        assert isinstance(rules, dict), (
            f"Priority '{priority_name}' in config/priorities.yml must be a mapping"
        )
        assert isinstance(rules.get("check_every"), int), (
            f"Priority '{priority_name}' must define an integer check_every"
        )
        assert rules["check_every"] > 0, (
            f"Priority '{priority_name}' check_every must be positive"
        )

        if "time_ranges" in rules:
            assert isinstance(rules["time_ranges"], list), (
                f"Priority '{priority_name}' time_ranges must be a list"
            )
            for time_range in rules["time_ranges"]:
                assert isinstance(time_range, dict), (
                    f"Priority '{priority_name}' time_ranges must contain mappings"
                )
                assert "start" in time_range and "end" in time_range, (
                    f"Priority '{priority_name}' time ranges must define start and end"
                )
                assert isinstance(time_range["start"], str), (
                    f"Priority '{priority_name}' time range start must be a string"
                )
                assert isinstance(time_range["end"], str), (
                    f"Priority '{priority_name}' time range end must be a string"
                )

                assert "days" in time_range, (
                    f"Priority '{priority_name}' time ranges must define days"
                )
                assert isinstance(time_range["days"], list), (
                    f"Priority '{priority_name}' time range days must be a list"
                )
                assert len(time_range["days"]) > 0, (
                    f"Priority '{priority_name}' time range days must not be empty"
                )
                for day_name in time_range["days"]:
                    assert isinstance(day_name, str), (
                        f"Priority '{priority_name}' time range days must contain strings"
                    )

    seen_urls = set()
    for category in categories:
        assert "sources" in category and isinstance(category["sources"], list)
        for source in category["sources"]:
            assert "feeds" in source and isinstance(source["feeds"], list)
            for feed in source["feeds"]:
                url = feed["url"]

                # Unique URLs
                assert url not in seen_urls, f"Duplicate URL: {url}"
                seen_urls.add(url)

                # Valid URL syntax
                assert is_url_valid_syntax(url), f"Invalid URL: {url}"

                # Valid keys only
                for key in feed:
                    assert key in VALID_KEYS, f"Invalid key '{key}' for feed {url}"

                # Wrappers exist and are a list
                if "wrappers" in feed:
                    names = feed["wrappers"]
                    assert isinstance(names, list), (
                        f"wrappers must be a list for feed {url}"
                    )
                    for name in names:
                        assert name in wrappers, (
                            f"Wrapper '{name}' is not defined in config/wrappers.yml"
                        )

                if "priority" in feed:
                    assert isinstance(feed["priority"], str), (
                        f"priority must be a string for feed {url}"
                    )
                    assert feed["priority"] in priorities, (
                        f"Priority '{feed['priority']}' is not defined in config/priorities.yml"
                    )

                if "folder" in feed:
                    assert isinstance(feed["folder"], str), (
                        f"folder must be a string for feed {url}"
                    )
                    assert feed["folder"] in known_folders, (
                        f"Folder '{feed['folder']}' for feed {url} is not defined in config/folders.yml"
                    )

