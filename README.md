# Instapaper RSS

Subscribe to RSS/Atom feeds and save items to [Instapaper](https://www.instapaper.com/).

## Quick start

1. Add your [Instapaper](https://www.instapaper.com/u) cookies to `config/cookies.yml`
2. Configure the RSS feeds you would like to subscribe to in `config/sources.yml`
3. Run command `make run`

## Sources YAML

In the `config/sources.yml` the following attributes may be used:

| Attribute | Description | Required |
| - | - | - |
| `url` | The URL to the RSS feed, a webpage which has an RSS feed, or an Instagram profile | Required |
| `description` | A description of what the source is | Optional |
| `wrappers` | Ordered list of wrapper names to apply to the entry URL | Optional |
| `blacklist_regex` | A regex pattern to match against the title of the RSS item. If it matches, the item will not be saved | Optional |
| `whitelist_regex` | A regex pattern to match against the title of the RSS item. If it matches, the item will be saved | Optional |
| `allowed_languages` | A list of allowable languages for the RSS item's title to be writen in, in order to be saved | Optional |

## Wrappers

Wrappers let you transform where an item is saved or viewed. Each template takes the original entry URL and nests it into another URL before it is sent to Instapaper.

Wrappers are defined in `config/wrappers.yml` as a mapping of wrapper names to URL templates containing `{url}`. The `{url}` placeholder is replaced with the entry URL and wrappers are applied in the order listed per feed. Two wrappers are included by default:

- `summarise`: Sends the entry URL to Perplexity with a summarisation prompt.
- `archive`: Saves via Archive.today
- `en_translate`: Translates the page via Google Translate to English.

## Settings

The application reads configuration values from `config/settings.yml`. The following keys are supported:

- `testing_mode`: When true the program will not actually save entries to Instapaper; it will only print what it would do. Useful for development and testing.
- `frequent_feed_threshold`: If a feed has more than this number of entries in the last month it will be treated as _frequent_ and the feed will be processed every time.
- `max_skips`: Controls many runs should occur before _infrequent_ feeds are processed (defined by `frequent_feed_threshold`). Infrequent feed processing is staggered by URL hash.

## Setting up Auto-run

A reccomended way to use this tool:

1. Set up an internet-connected always-on computer (such as a Raspberry Pi)
2. Unstall `uv` on that computer
3. Update `REMOTE_LOGIN_IDENTIFIER` and `REMOTE_PATH` in the `Makefile` to your choice
4. Run command `make deploy`
5. Add crontab `0 6-21 * * * cd /home/pi/Documents/instapaper-rss && PATH="/home/pi/.local/bin:$PATH" make run > /home/pi/log.txt 2>&1`
