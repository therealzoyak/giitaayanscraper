# Giitaayan Song Scraper
**CWL 207 – Indian Cinema in Context**

Scrapes song metadata from [new.giitaayan.com](https://new.giitaayan.com) and enriches it with IMDb film IDs using the TMDb API.

---

## What This Does

1. Calls the Giitaayan API directly (no browser needed) to collect all ~3,445 songs from 1930–2025
2. Looks up each unique film on TMDb to get its IMDb `tt` ID
3. Saves everything to `giitaayan_songs.csv`

---
## Included
1. The code file and the final dataset
---

## Setup

```bash
pip install requests pandas rapidfuzz
```

---

## Run

```bash
python3 giitaayan_scraper.py
```

---

## Output

`giitaayan_songs.csv` with the following columns:

| song_title | album | year | singer | lyricist | composer | imdb_id |
|---|---|---|---|---|---|---|
| saa.Nwar waalaa vahii re | Pukaar | 1939 | Naseem, Sardar Akhtar | Kamal Amrohi | Mir Sahab | tt0032599 |

---

## How It Works

Giitaayan uses a Supabase backend. By inspecting the site's network requests, we found the API endpoint it calls to load songs:

```
POST https://db.giitaayan.com/rest/v1/rpc/search_song_stats
```

We query this endpoint year by year (1930–2025) using `search_terms: "year:XXXX"` to collect all songs. IMDb IDs are then resolved using the TMDb API with fuzzy title matching.

