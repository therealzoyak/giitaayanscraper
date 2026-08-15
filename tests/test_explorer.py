import unittest

import pandas as pd

from explorer import filter_songs, numeric_year, prepare_data, top_values


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.frame = prepare_data(
            pd.DataFrame(
                [
                    {
                        "song_title": "Song A",
                        "album": "Film One",
                        "year": "1952",
                        "singer": "Asha",
                        "lyricist": "Sahir",
                        "composer": "Ravi",
                        "imdb_id": "tt123",
                    },
                    {
                        "song_title": "Song B",
                        "album": "Film Two",
                        "year": "1960s",
                        "singer": "Lata",
                        "lyricist": "Sahir",
                        "composer": "Ravi",
                        "imdb_id": "",
                    },
                ]
            )
        )

    def test_numeric_year_accepts_exact_year_and_decade(self):
        self.assertEqual(numeric_year("1952"), 1952)
        self.assertEqual(numeric_year("1960s"), 1960)
        self.assertIsNone(numeric_year("unknown"))

    def test_free_text_searches_across_fields(self):
        result = filter_songs(self.frame, query="film two")
        self.assertEqual(result["song_title"].tolist(), ["Song B"])

    def test_filters_people_and_year(self):
        result = filter_songs(self.frame, year_range=(1950, 1959), singers=["Asha"])
        self.assertEqual(result["song_title"].tolist(), ["Song A"])

    def test_top_values_counts_people(self):
        result = top_values(self.frame, "lyricist")
        self.assertEqual(result.iloc[0].to_dict(), {"lyricist": "Sahir", "songs": 2})


if __name__ == "__main__":
    unittest.main()
