"""
Giitaayan Song Scraper + IMDb ID Matcher
CWL 207 - Indian Cinema in Context

Requirements:
    pip install requests pandas rapidfuzz

Usage:
    python3 giitaayan_scraper.py

Output:
    giitaayan_songs.csv
"""

import time
import requests
import pandas as pd
from rapidfuzz import fuzz

# ── Giitaayan API config ──────────────────────────────────────────
API_URL = "https://db.giitaayan.com/rest/v1/rpc/search_song_stats"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndyanptZXJuY2FndHV5aHVicGFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI0MjI2ODYsImV4cCI6MjA0Nzk5ODY4Nn0.YxLVtKQIcBH8RRSMdMDRT1_p_5_pZFyOQx37NuhHZ6U",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndyanptZXJuY2FndHV5aHVicGFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI0MjI2ODYsImV4cCI6MjA0Nzk5ODY4Nn0.YxLVtKQIcBH8RRSMdMDRT1_p_5_pZFyOQx37NuhHZ6U"
}

START_YEAR = 1930
END_YEAR   = 2025

# ── TMDb / IMDb config (your friend's code) ───────────────────────
TMDB_API_KEY   = "7075c36b5198aa7c004aedb756385408"
TMDB_BASE      = "https://api.themoviedb.org/3"
MIN_MATCH_SCORE = 80
YEAR_TOLERANCE  = 1
_imdb_cache: dict = {}

def _score(query_title, query_year, cand):
    name = max(
        fuzz.token_set_ratio(query_title.lower(), (cand.get("title") or "").lower()),
        fuzz.token_set_ratio(query_title.lower(), (cand.get("original_title") or "").lower()),
    )
    rd = cand.get("release_date") or ""
    cand_year = int(rd[:4]) if len(rd) >= 4 and rd[:4].isdigit() else None
    penalty = 0.0
    if query_year and cand_year and abs(cand_year - query_year) > YEAR_TOLERANCE:
        penalty = min(40.0, abs(cand_year - query_year) * 5.0)
    elif query_year and not cand_year:
        penalty = 5.0
    bonus = 3.0 if (cand.get("original_language") or "") == "hi" else 0.0
    return name - penalty + bonus

def get_imdb_id(film, year=None):
    if not film:
        return ""
    key = (film.strip().lower(), year)
    if key in _imdb_cache:
        return _imdb_cache[key]
    params = {"api_key": TMDB_API_KEY, "query": film, "include_adult": "false"}
    if year:
        params["year"] = year
    r = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=15, verify=False)
    results = (r.json() if r.ok else {}).get("results") or []
    if not results and year:
        params.pop("year")
        r = requests.get(f"{TMDB_BASE}/search/movie", params=params, timeout=15, verify=False)
        results = (r.json() if r.ok else {}).get("results") or []
    if not results:
        _imdb_cache[key] = ""
        return ""
    best = max(results, key=lambda c: _score(film, year, c))
    if _score(film, year, best) < MIN_MATCH_SCORE:
        _imdb_cache[key] = ""
        return ""
    r2 = requests.get(f"{TMDB_BASE}/movie/{best['id']}/external_ids", params={"api_key": TMDB_API_KEY}, timeout=15, verify=False)
    imdb_id = (r2.json() if r2.ok else {}).get("imdb_id") or ""
    _imdb_cache[key] = imdb_id
    return imdb_id

# ── Step 1: Scrape Giitaayan ──────────────────────────────────────
print("Scraping Giitaayan...")
all_songs = []

for year in range(START_YEAR, END_YEAR + 1):
    try:
        r = requests.post(API_URL, json={"search_terms": f"year:{year}", "similarity_threshold": 0.1}, headers=HEADERS, timeout=15)
        songs = r.json() if r.ok else []
    except Exception as e:
        print(f"  Error {year}: {e}")
        songs = []

    if songs:
        print(f"{year}: {len(songs)} songs")
        for s in songs:
            all_songs.append({
                "song_title": s.get("song_title", "N/A"),
                "album":      s.get("album",      "N/A"),
                "year":       s.get("year",        year),
                "singer":     s.get("singer",     "N/A"),
                "lyricist":   s.get("lyricist",   "N/A"),
                "composer":   s.get("composer",   "N/A"),
                "imdb_id":    "",
            })
    time.sleep(0.3)

print(f"\nScraped {len(all_songs)} songs. Now looking up IMDb IDs...")

# ── Step 2: Add IMDb IDs (cached per unique film) ─────────────────
film_cache = {}
for i, song in enumerate(all_songs):
    album = song["album"]
    year  = song["year"]
    if album == "N/A":
        continue
    key = (album, year)
    if key not in film_cache:
        print(f"  [{len(film_cache)+1}] {album} ({year})")
        yr = int(year) if str(year).isdigit() else None
    film_cache[key] = get_imdb_id(album, yr)
    song["imdb_id"] = film_cache[key]

# ── Step 3: Save ──────────────────────────────────────────────────
df = pd.DataFrame(all_songs)
df.to_csv("giitaayan_songs.csv", index=False, encoding="utf-8-sig")
print(f"\nDone! Saved {len(df)} songs to giitaayan_songs.csv")
print(df.head(10).to