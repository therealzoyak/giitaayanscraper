"""Pure data helpers for the Giitaayan Explorer interface."""

from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd

SEARCH_COLUMNS = ["song_title", "album", "singer", "lyricist", "composer"]


def numeric_year(value: object) -> int | None:
    """Extract the first four-digit year from exact years or decade labels."""
    match = re.search(r"(?:18|19|20)\d{2}", str(value))
    return int(match.group()) if match else None


def prepare_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize the checked-in CSV for filtering and display."""
    result = frame.copy()
    for column in SEARCH_COLUMNS + ["imdb_id"]:
        if column not in result:
            result[column] = ""
        result[column] = result[column].fillna("").astype(str).str.strip()

    if "year" not in result:
        result["year"] = ""
    result["year_numeric"] = result["year"].map(numeric_year)
    result["decade"] = result["year_numeric"].map(
        lambda year: f"{(int(year) // 10) * 10}s" if pd.notna(year) else "Unknown"
    )
    result["imdb_url"] = result["imdb_id"].map(
        lambda imdb_id: f"https://www.imdb.com/title/{imdb_id}/" if imdb_id.startswith("tt") else ""
    )
    return result


def filter_songs(
    frame: pd.DataFrame,
    query: str = "",
    year_range: tuple[int, int] | None = None,
    singers: Iterable[str] = (),
    composers: Iterable[str] = (),
    lyricists: Iterable[str] = (),
) -> pd.DataFrame:
    """Apply the explorer's free-text, year, and people filters."""
    mask = pd.Series(True, index=frame.index)

    if query.strip():
        needle = re.escape(query.strip())
        searchable = frame[SEARCH_COLUMNS].agg(" ".join, axis=1)
        mask &= searchable.str.contains(needle, case=False, regex=True, na=False)

    if year_range:
        start, end = year_range
        mask &= frame["year_numeric"].between(start, end, inclusive="both")

    for column, selected in (
        ("singer", list(singers)),
        ("composer", list(composers)),
        ("lyricist", list(lyricists)),
    ):
        if selected:
            mask &= frame[column].isin(selected)

    return frame.loc[mask].copy()


def top_values(frame: pd.DataFrame, column: str, limit: int = 12) -> pd.DataFrame:
    """Return the most common non-empty values in a people column."""
    values = frame[column].replace({"": pd.NA, "N/A": pd.NA}).dropna()
    return values.value_counts().head(limit).rename_axis(column).reset_index(name="songs")
