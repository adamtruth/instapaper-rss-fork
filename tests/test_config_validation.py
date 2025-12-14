from urllib.parse import urlparse

import yaml

VALID_KEYS = {
    "url",
    "description",
    "wrappers",
    "blacklist_regex",
    "whitelist_regex",
    "allowed_languages",
}


def is_url_valid_syntax(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def test_wrappers_yaml_is_mapping():
    with open("config/wrappers.yml", "r") as f:
        wrappers = yaml.safe_load(f)
    assert isinstance(wrappers, dict), "config/wrappers.yml must be a mapping"


def test_sources_yaml_structure_and_constraints():
    with open("config/sources.yml", "r") as f:
        categories = yaml.safe_load(f)
    with open("config/wrappers.yml", "r") as f:
        wrappers = yaml.safe_load(f)

    assert isinstance(categories, list), "config/sources.yml must be a list"
    assert isinstance(wrappers, dict), "config/wrappers.yml must be a mapping"

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
