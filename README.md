# Giitaayan Explorer

I wanted to study Hindi film music as data, but the dataset I needed did not exist in a form I could actually explore. So I built one.

Giitaayan Explorer collects song credits from the Giitaayan archive, matches films to IMDb identifiers, and turns the resulting dataset into a searchable interface for moving across decades, singers, lyricists, composers, and films.

The checked-in dataset contains **2,258 songs** spanning the 1930s through 1985, including **1,206 IMDb matches**. The archive changes over time, so a fresh scrape may produce different counts and a wider year range.

## Explore the archive

The Streamlit interface includes:

- full-text search across songs, films, singers, lyricists, and composers
- year, singer, composer, and lyricist filters
- linked IMDb film pages
- a decade view that responds to the current filters
- leaderboards for the people behind the music
- downloadable search results and a random-song discovery view

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## How the data pipeline works

1. Query Giitaayan's public Supabase RPC one year at a time.
2. Normalize song, film, year, singer, lyricist, and composer fields.
3. Search TMDb for each unique film and score candidates using title similarity, release-year distance, and original language.
4. Resolve the best candidate to its IMDb ID and cache repeated film lookups.
5. Save the result as UTF-8 CSV for the explorer and downstream analysis.

The matcher rejects low-confidence candidates instead of quietly attaching a plausible-but-wrong film.

## Rebuild the dataset

Copy `.env.example` to `.env` or export the two variables in your shell. API keys are intentionally never committed.

```bash
export GIITAAYAN_API_KEY="..."
export TMDB_API_KEY="..."
python giitaayan_scraper.py --start-year 1930 --end-year 2025
```

To collect Giitaayan records without IMDb enrichment:

```bash
python giitaayan_scraper.py --skip-imdb
```

## Data notes

- Giitaayan's transliteration is preserved rather than silently modernized.
- Decade labels such as `1930s` are retained in the source year field and normalized separately for charts.
- A blank IMDb ID means the matcher did not find a candidate above the confidence threshold.
- This is an exploratory cultural dataset, not a claim of complete Hindi-cinema coverage.

## Tests

```bash
python -m unittest discover -s tests
```

The tests cover year normalization, cross-field search, compound filters, and people-frequency summaries.

## Origin

I began this project while taking **CWL 207: Indian Cinema in Context at UIUC**. The course supplied the question, not the software: I designed the API workflow, film matching, dataset, and explorer to investigate it.
