#!/usr/bin/env python3
"""Bygg index.html fra episodes/*.json.

Bruker bare Python 3 sitt standardbibliotek. Kjør fra hvor som helst:

    python3 build.py

Videoen på YouTube har 12,333 sekunder intro før podkastlyden. Tidskoden
i siden er starttiden i lyden (mm:ss). YouTube-lenken får ?t= lik
floor(start + 12,333).
"""

from __future__ import annotations

import html
import json
import math
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EPISODES_DIR = ROOT / "episodes"
OUTPUT = ROOT / "index.html"

YOUTUBE_INTRO_SECONDS = 12.333

LINK_LABELS = (
    ("spotify", "Spotify"),
    ("youtube", "YouTube"),
    ("x", "X"),
)
KNOWN_LINKS = {key for key, _label in LINK_LABELS}

WEEKDAYS = (
    "mandag",
    "tirsdag",
    "onsdag",
    "torsdag",
    "fredag",
    "lørdag",
    "søndag",
)
MONTHS = (
    "januar",
    "februar",
    "mars",
    "april",
    "mai",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "desember",
)


def fail(message: str) -> None:
    sys.exit(message)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def require_str(data: dict, key: str, where: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{where}: feltet {key!r} må være en ikke-tom tekst")
    return value.strip()


def optional_url(value: object, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        fail(f"{where}: lenke må være tekst eller null")
    text = value.strip()
    if not text:
        return None
    if not text.startswith(("https://", "http://")):
        fail(f"{where}: lenke må starte med http:// eller https:// ({text})")
    return text


def format_date(iso: str) -> str:
    try:
        year, month, day = (int(part) for part in iso.split("-"))
        current = date(year, month, day)
    except ValueError:
        fail(f"Ugyldig dato: {iso}")
    weekday = WEEKDAYS[current.weekday()].capitalize()
    return f"{weekday} {current.day}. {MONTHS[current.month - 1]} {current.year}"


def format_timestamp(start: float) -> str:
    total = math.floor(start)
    minutes, seconds = divmod(total, 60)
    return f"{minutes:02d}:{seconds:02d}"


def youtube_time(start: float) -> int:
    return math.floor(start + YOUTUBE_INTRO_SECONDS)


def with_time(url: str, seconds: int) -> str:
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}t={seconds}"


def load_episode(path: Path) -> dict:
    where = f"episodes/{path.name}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"{where}: ugyldig JSON ({error})")
    if not isinstance(data, dict):
        fail(f"{where}: fila må inneholde et JSON-objekt")

    episode_date = require_str(data, "date", where)
    if path.stem != episode_date:
        fail(f"{where}: date er {episode_date!r}, men filnavnet er {path.stem!r}")
    format_date(episode_date)

    title = require_str(data, "title", where)
    description = require_str(data, "description", where)

    links_raw = data.get("links", {})
    if not isinstance(links_raw, dict):
        fail(f"{where}: links må være et objekt")
    unknown = sorted(set(links_raw) - KNOWN_LINKS)
    if unknown:
        fail(f"{where}: ukjente lenker {unknown}. Bruk spotify, youtube og x")
    links = {
        key: optional_url(links_raw.get(key), f"{where}: links.{key}")
        for key in KNOWN_LINKS
    }

    topics_raw = data.get("topics")
    if not isinstance(topics_raw, list) or not topics_raw:
        fail(f"{where}: topics må være en ikke-tom liste")

    topics = []
    for index, topic in enumerate(topics_raw, start=1):
        topic_where = f"{where}: sak {index}"
        if not isinstance(topic, dict):
            fail(f"{topic_where}: må være et objekt")
        topic_title = require_str(topic, "title", topic_where)
        start = topic.get("start")
        if isinstance(start, bool) or not isinstance(start, (int, float)):
            fail(f"{topic_where}: start må være antall sekunder (tall)")
        if start < 0:
            fail(f"{topic_where}: start kan ikke være negativ")

        sources_raw = topic.get("sources")
        if not isinstance(sources_raw, list):
            fail(f"{topic_where}: sources må være en liste")
        sources = []
        for source_index, source in enumerate(sources_raw, start=1):
            source_where = f"{topic_where}, kilde {source_index}"
            if not isinstance(source, dict):
                fail(f"{source_where}: må være et objekt med name og url")
            name = require_str(source, "name", source_where)
            url = optional_url(source.get("url"), source_where)
            if url is None:
                fail(f"{source_where}: url mangler")
            sources.append({"name": name, "url": url})
        topics.append({"title": topic_title, "start": float(start), "sources": sources})

    return {
        "date": episode_date,
        "title": title,
        "description": description,
        "links": links,
        "topics": topics,
    }


def external_link(
    url: str,
    text: str,
    aria_label: str | None = None,
    class_name: str | None = None,
) -> str:
    label = f' aria-label="{esc(aria_label)}"' if aria_label else ""
    classes = f' class="{esc(class_name)}"' if class_name else ""
    return (
        f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer"{classes}{label}>'
        f"{esc(text)}</a>"
    )


def render_timestamp(start: float, youtube: str | None) -> str:
    stamp = format_timestamp(start)
    if not youtube:
        return f'<span class="tid">{esc(stamp)}</span>'
    url = with_time(youtube, youtube_time(start))
    return external_link(url, stamp, f"Spill fra {stamp} på YouTube", "tid")


def render_sources(sources: list[dict]) -> str:
    if not sources:
        return ""
    items = ", ".join(external_link(source["url"], source["name"]) for source in sources)
    return f'<p class="kilder"><span class="etikett">Kilder: </span>{items}</p>'


def render_episode(episode: dict) -> str:
    links = episode["links"]
    platform_items = []
    for key, label in LINK_LABELS:
        url = links.get(key)
        if url:
            platform_items.append(f"<li>{external_link(url, label)}</li>")
    platforms = ""
    if platform_items:
        platforms = '<ul class="plattformer">\n' + "\n".join(platform_items) + "\n</ul>"

    topics = []
    for topic in episode["topics"]:
        topics.append(
            "\n".join(
                [
                    "<li>",
                    '<div class="sak">',
                    render_timestamp(topic["start"], links.get("youtube")),
                    "<div>",
                    f"<h3>{esc(topic['title'])}</h3>",
                    render_sources(topic["sources"]),
                    "</div>",
                    "</div>",
                    "</li>",
                ]
            )
        )

    return "\n".join(
        [
            f'<article id="{esc(episode["date"])}">',
            f"<h2>{esc(episode['title'])}</h2>",
            f'<p class="beskrivelse">{esc(episode["description"])}</p>',
            platforms,
            '<ul class="saker">',
            "\n".join(topics),
            "</ul>",
            "</article>",
        ]
    )


def render_page(episodes: list[dict]) -> str:
    toc = "\n".join(
        f'<li><a href="#{esc(episode["date"])}">{esc(format_date(episode["date"]))}</a></li>'
        for episode in episodes
    )
    body = "\n".join(render_episode(episode) for episode in episodes)
    return f"""<!DOCTYPE html>
<!-- Generert av build.py fra episodes/*.json. Ikke rediger for hånd. -->
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bekken – shownotes</title>
<meta name="description" content="Shownotes for den daglige nyhetspodkasten Bekken.">
<style>
:root {{
  --bg: #f3f0e8;
  --ink: #1c1915;
  --muted: #4e4942;
  --line: #ddd6c8;
  --link: #0d3f66;
  --time: #7a3418;
  --focus: #1f4d3a;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 1.0625rem;
  line-height: 1.5;
  overflow-wrap: break-word;
}}
.side {{
  max-width: 40rem;
  margin: 0 auto;
  padding: 1.75rem 1.25rem 4rem;
}}
h1 {{
  margin: 0;
  font-size: clamp(2.1rem, 8vw, 2.75rem);
  line-height: 1.05;
  letter-spacing: -0.03em;
}}
.intro {{
  margin: 0.6rem 0 0;
  color: var(--muted);
}}
.merknad {{
  margin: 0.75rem 0 0;
  color: var(--muted);
  font-size: 0.95rem;
}}
nav {{
  margin-top: 1.75rem;
}}
h2 {{
  margin: 0;
  font-size: 1.35rem;
  line-height: 1.25;
  letter-spacing: -0.02em;
}}
.toc {{
  list-style: none;
  margin: 0.6rem 0 0;
  padding: 0;
}}
.toc a {{
  display: block;
  padding: 0.45rem 0;
  color: var(--link);
}}
article {{
  margin-top: 2.25rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--ink);
  scroll-margin-top: 1rem;
}}
.beskrivelse {{
  margin: 0.8rem 0 0;
}}
.plattformer {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
}}
.plattformer a {{
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fffdf8;
  color: var(--link);
  text-decoration: none;
}}
.plattformer a:hover {{
  border-color: var(--link);
}}
.saker {{
  list-style: none;
  margin: 1.25rem 0 0;
  padding: 0;
}}
.saker > li + li {{
  margin-top: 1rem;
}}
.sak {{
  display: grid;
  grid-template-columns: 4.25rem minmax(0, 1fr);
  column-gap: 0.75rem;
  align-items: start;
}}
.tid {{
  font-family: ui-monospace, "Cascadia Mono", "Segoe UI Mono", monospace;
  font-variant-numeric: tabular-nums;
  font-size: 0.95rem;
  line-height: 1.45;
  color: var(--time);
  padding-top: 0.12rem;
}}
a.tid {{
  text-decoration-thickness: 1px;
  text-underline-offset: 0.15em;
}}
h3 {{
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.35;
}}
.kilder {{
  margin: 0.3rem 0 0;
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.5;
}}
a {{
  color: var(--link);
}}
a:hover {{
  text-decoration-thickness: 2px;
}}
:focus-visible {{
  outline: 2px solid var(--focus);
  outline-offset: 3px;
}}
</style>
</head>
<body>
<div class="side">
<header>
<h1>Bekken</h1>
<p class="intro">Shownotes for den daglige nyhetspodkasten. Nyeste episode øverst.</p>
<p class="merknad">Tidskoden viser hvor saken starter i podkasten. Der episoden ligger på YouTube, åpner tidskoden videoen på samme sted.</p>
</header>
<nav aria-label="Innhold">
<h2>Innhold</h2>
<ul class="toc">
{toc}
</ul>
</nav>
<main>
{body}
</main>
</div>
</body>
</html>
"""


def main() -> None:
    paths = sorted(EPISODES_DIR.glob("*.json"))
    if not paths:
        fail(f"Fant ingen JSON-filer i {EPISODES_DIR}")
    episodes = [load_episode(path) for path in paths]
    episodes.sort(key=lambda episode: episode["date"], reverse=True)
    OUTPUT.write_text(render_page(episodes), encoding="utf-8")
    print(f"Skrev {OUTPUT.name} med {len(episodes)} episoder.")


if __name__ == "__main__":
    main()
