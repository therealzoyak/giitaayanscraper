# Giitaayan Song Scraper
**FOR CWL 207 – Indian Cinema in Context**

Scrapes song metadata from [new.giitaayan.com](https://new.giitaayan.com) and enriches it with IMDb film IDs using Cinemagoer.

---

## Setup

```bash
pip install selenium cinemagoer pandas webdriver-manager
```

You also need **Google Chrome** installed on your computer (the scraper controls it automatically).

---

## Run

```bash
python giitaayan_scraper.py
```

This will:
1. Open Giitaayan in a headless Chrome browser
2. Scroll through and collect all songs
3. Look up each film on IMDb to get its `tt` ID
4. Save everything to `giitaayan_songs.csv`

---

## Output

A CSV file (`giitaayan_songs.csv`) with columns like:

| song_title | film | singer | imdb_id |
|---|---|---|---|
| Tere Bina | Guru | Chinmayi | tt0449994 |

---

## ⚠️ Important: Updating the CSS Selectors

Because Giitaayan is a React app, the HTML it generates uses
auto-generated class names that **you need to find yourself**.

Here's how:

1. Open [https://new.giitaayan.com/](https://new.giitaayan.com/) in Chrome
2. Right-click on a song title → click **Inspect**
3. In the DevTools panel, look at what HTML element wraps each song
4. Note the class name or tag (e.g. `<div class="song-item">`)
5. Update this line in `giitaayan_scraper.py`:

```python
song_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='song']")
```

Replace `"[class*='song']"` with whatever selector matches what you found.

---

## Finding the Hidden API (Easier Method)

Giitaayan likely calls its own backend API to load songs. You can find it:

1. Open [https://new.giitaayan.com/](https://new.giitaayan.com/) in Chrome
2. Open DevTools → **Network** tab
3. Filter by **Fetch/XHR**
4. Refresh the page and scroll
5. Look for requests to URLs like `/api/songs` or `/api/giits`
6. Click one → look at the **Response** tab to see the JSON

If you find a clean API endpoint, you can replace the Selenium code
with a simple `requests.get(url)` call — much faster and more reliable.

---

## Group Info
- Course: CWL 207
- Task: Scrape Giitaayan (~3500 songs) + Add IMDb IDs
- Due: April 30, 2026
