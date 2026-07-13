import unittest

from recommendation import recommend


class RecommendationTests(unittest.TestCase):
    def test_missing_measurements(self):
        self.assertEqual(
            recommend({"temperature": None, "humidity": None}),
            "Климат маалыматтары жеткиликтүү эмес.",
        )

    def test_normal_climate(self):
        self.assertEqual(
            recommend({"temperature": 20, "humidity": 50}),
            "Климат нормалдуу.",
        )

    def test_combines_humidity_and_heat_recommendations(self):
        result = recommend({"temperature": 40, "humidity": 90})
        self.assertIn("Грибок", result)
        self.assertIn("сугаруу", result)

    def test_cold_recommendation(self):
        self.assertIn(
            "сууктан",
            recommend({"temperature": 0, "humidity": 50}),
        )


if __name__ == "__main__":
    unittest.main()
