"""Build a searchable Giitaayan song dataset and optionally enrich films with IMDb IDs.

The scraper talks to the same public Supabase RPC used by Giitaayan's web app.
Credentials are read from environment variables so the repository never contains
private API keys.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from rapidfuzz import fuzz

GIITAAYAN_API_URL = "https://db.giitaayan.com/rest/v1/rpc/search_song_stats"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
MIN_MATCH_SCORE = 80
YEAR_TOLERANCE = 1


def build_headers(api_key: str) -> dict[str, str]:
    """Return the headers required by Giitaayan's Supabase endpoint."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }


def fetch_year(
    session: requests.Session,
    year: int,
    giitaayan_api_key: str,
) -> list[dict[str, Any]]:
    """Fetch one year of Giitaayan records with explicit failure reporting."""
    response = session.post(
        GIITAAYAN_API_URL,
        json={"search_terms": f"year:{year}", "similarity_threshold": 0.1},
        headers=build_headers(giitaayan_api_key),
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected Giitaayan response for {year}: {type(payload).__name__}")
    return payload


def _candidate_score(title: str, year: int | None, candidate: dict[str, Any]) -> float:
    candidate_title = candidate.get("title") or ""
    original_title = candidate.get("original_title") or ""
    title_score = max(
        fuzz.token_set_ratio(title.casefold(), candidate_title.casefold()),
        fuzz.token_set_ratio(title.casefold(), original_title.casefold()),
    )

    release_date = candidate.get("release_date") or ""
    candidate_year = int(release_date[:4]) if release_date[:4].isdigit() else None
    penalty = 0.0
    if year and candidate_year and abs(candidate_year - year) > YEAR_TOLERANCE:
        penalty = min(40.0, abs(candidate_year - year) * 5.0)
    elif year and not candidate_year:
        penalty = 5.0

    language_bonus = 3.0 if candidate.get("original_language") == "hi" else 0.0
    return title_score - penalty + language_bonus


def get_imdb_id(
    session: requests.Session,
    film: str,
    year: int | None,
    tmdb_api_key: str,
    cache: dict[tuple[str, int | None], str],
) -> str:
    """Resolve a film to an IMDb ID using fuzzy title and release-year matching."""
    if not film or film in {"N/A", "(Non-film)"}:
        return ""

    key = (film.strip().casefold(), year)
    if key in cache:
        return cache[key]

    params: dict[str, Any] = {
        "api_key": tmdb_api_key,
        "query": film,
        "include_adult": "false",
    }
    if year:
        params["year"] = year

    response = session.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=20)
    response.raise_for_status()
    results = response.json().get("results") or []

    if not results and year:
        params.pop("year")
        response = session.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=20)
        response.raise_for_status()
        results = response.json().get("results") or []

    if not results:
        cache[key] = ""
        return ""

    best = max(results, key=lambda item: _candidate_score(film, year, item))
    if _candidate_score(film, year, best) < MIN_MATCH_SCORE:
        cache[key] = ""
        return ""

    response = session.get(
        f"{TMDB_BASE_URL}/movie/{best['id']}/external_ids",
        params={"api_key": tmdb_api_key},
        timeout=20,
    )
    response.raise_for_status()
    cache[key] = response.json().get("imdb_id") or ""
    return cache[key]


def scrape(
    start_year: int,
    end_year: int,
    giitaayan_api_key: str,
    tmdb_api_key: str | None,
    delay_seconds: float,
) -> pd.DataFrame:
    """Collect Giitaayan songs and optionally enrich unique films with IMDb IDs."""
    session = requests.Session()
    records: list[dict[str, Any]] = []

    for year in range(start_year, end_year + 1):
        try:
            songs = fetch_year(session, year, giitaayan_api_key)
        except (requests.RequestException, ValueError) as exc:
            print(f"{year}: skipped ({exc})")
            continue

        print(f"{year}: {len(songs)} songs")
        records.extend(
            {
                "song_title": song.get("song_title") or "N/A",
                "album": song.get("album") or "N/A",
                "year": song.get("year") or year,
                "singer": song.get("singer") or "N/A",
                "lyricist": song.get("lyricist") or "N/A",
                "composer": song.get("composer") or "N/A",
                "imdb_id": "",
            }
            for song in songs
        )
        time.sleep(delay_seconds)

    if not tmdb_api_key:
        return pd.DataFrame(records)

    film_cache: dict[tuple[str, int | None], str] = {}
    for index, song in enumerate(records, start=1):
        raw_year = str(song["year"])
        year = int(raw_year) if raw_year.isdigit() else None
        try:
            song["imdb_id"] = get_imdb_id(
                session,
                str(song["album"]),
                year,
                tmdb_api_key,
                film_cache,
            )
        except requests.RequestException as exc:
            print(f"IMDb lookup failed for {song['album']}: {exc}")
        if index % 100 == 0:
            print(f"IMDb enrichment: {index}/{len(records)} songs")

    return pd.DataFrame(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=1930)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--output", type=Path, default=Path("giitaayan_songs.csv"))
    parser.add_argument("--skip-imdb", action="store_true")
    parser.add_argument("--delay", type=float, default=0.3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    giitaayan_api_key = os.getenv("GIITAAYAN_API_KEY", "").strip()
    if not giitaayan_api_key:
        raise SystemExit("Set GIITAAYAN_API_KEY before running the scraper.")

    tmdb_api_key = None if args.skip_imdb else os.getenv("TMDB_API_KEY", "").strip() or None
    if not args.skip_imdb and not tmdb_api_key:
        print("TMDB_API_KEY is missing; continuing without IMDb enrichment.")

    frame = scrape(
        args.start_year,
        args.end_year,
        giitaayan_api_key,
        tmdb_api_key,
        args.delay,
    )
    frame.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"Saved {len(frame):,} songs to {args.output}")
    if not frame.empty:
        print(frame.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
