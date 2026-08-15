"""Streamlit interface for exploring the Giitaayan song dataset."""

from pathlib import Path

import pandas as pd
import streamlit as st

from explorer import filter_songs, prepare_data, top_values

DATA_PATH = Path(__file__).with_name("giitaayan_songs.csv")

st.set_page_config(page_title="Giitaayan Explorer", page_icon="🎞️", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1280px;}
    h1, h2, h3 {letter-spacing: -0.035em;}
    [data-testid="stMetric"] {background: #fff8ee; border: 1px solid #efd9b7; padding: 1rem; border-radius: 1rem;}
    [data-testid="stMetric"] * {color: #251c17 !important;}
    [data-testid="stSidebar"] {background: #fffaf3;}
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {color: #251c17 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return prepare_data(pd.read_csv(path))


data = load_data(DATA_PATH)

st.title("Giitaayan Explorer")
st.caption(
    "A searchable lens into Hindi film music history—songs, films, singers, "
    "lyricists, and composers from the Giitaayan archive."
)

valid_years = data["year_numeric"].dropna().astype(int)
year_bounds = (int(valid_years.min()), int(valid_years.max()))

with st.sidebar:
    st.header("Find a song")
    query = st.text_input("Search everything", placeholder="song, film, singer, lyricist…")
    year_range = st.slider("Year", year_bounds[0], year_bounds[1], year_bounds)
    singers = st.multiselect("Singer", sorted(value for value in data["singer"].unique() if value))
    composers = st.multiselect("Composer", sorted(value for value in data["composer"].unique() if value))
    lyricists = st.multiselect("Lyricist", sorted(value for value in data["lyricist"].unique() if value))
    st.caption(
        "The dataset keeps Giitaayan's original transliteration so search works "
        "with the archive's spellings."
    )

effective_year_range = None if year_range == year_bounds else year_range
filtered = filter_songs(data, query, effective_year_range, singers, composers, lyricists)
matched_imdb = filtered["imdb_url"].ne("").sum()

metric_columns = st.columns(4)
metric_columns[0].metric("Songs", f"{len(filtered):,}")
metric_columns[1].metric("Films / albums", f"{filtered['album'].nunique():,}")
metric_columns[2].metric(
    "People credited",
    f"{pd.concat([filtered['singer'], filtered['composer'], filtered['lyricist']]).replace('', pd.NA).nunique():,}",
)
metric_columns[3].metric("IMDb matched", f"{matched_imdb / max(len(filtered), 1):.0%}")

explore_tab, timeline_tab, people_tab, surprise_tab = st.tabs(
    ["Explore", "Across the decades", "People behind the music", "Surprise me"]
)

with explore_tab:
    st.subheader(f"{len(filtered):,} matching songs")
    display = filtered[
        ["song_title", "album", "year", "singer", "lyricist", "composer", "imdb_url"]
    ].rename(
        columns={
            "song_title": "Song",
            "album": "Film / album",
            "year": "Year",
            "singer": "Singer",
            "lyricist": "Lyricist",
            "composer": "Composer",
            "imdb_url": "IMDb",
        }
    )
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        height=560,
        column_config={"IMDb": st.column_config.LinkColumn("IMDb", display_text="open ↗")},
    )
    st.download_button(
        "Download these results",
        display.to_csv(index=False).encode("utf-8"),
        "giitaayan_search_results.csv",
        "text/csv",
    )

with timeline_tab:
    decade_counts = (
        filtered.loc[filtered["decade"] != "Unknown", "decade"]
        .value_counts()
        .sort_index()
        .rename("songs")
    )
    st.subheader("Songs represented by decade")
    st.bar_chart(decade_counts, color="#bf5b3d")
    st.caption(
        "Counts reflect the current filters and the coverage of the checked-in "
        "Giitaayan dataset—not total industry output."
    )

with people_tab:
    singer_column, composer_column, lyricist_column = st.columns(3)
    with singer_column:
        st.subheader("Singers")
        st.dataframe(top_values(filtered, "singer"), hide_index=True, width="stretch")
    with composer_column:
        st.subheader("Composers")
        st.dataframe(top_values(filtered, "composer"), hide_index=True, width="stretch")
    with lyricist_column:
        st.subheader("Lyricists")
        st.dataframe(top_values(filtered, "lyricist"), hide_index=True, width="stretch")

with surprise_tab:
    if filtered.empty:
        st.info("Loosen a filter and I’ll find something.")
    else:
        if "random_seed" not in st.session_state:
            st.session_state.random_seed = 1
        if st.button("Another song"):
            st.session_state.random_seed += 1
        song = filtered.sample(1, random_state=st.session_state.random_seed).iloc[0]
        st.subheader(song["song_title"])
        st.write(f"**{song['album']}** · {song['year']}")
        st.write(
            f"Sung by {song['singer']}  \nWritten by {song['lyricist']}  "
            f"\nComposed by {song['composer']}"
        )
        if song["imdb_url"]:
            st.link_button("Open the film on IMDb", song["imdb_url"])
