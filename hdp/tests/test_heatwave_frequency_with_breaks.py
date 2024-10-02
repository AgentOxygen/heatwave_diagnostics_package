from hdp import heat_stats
import numpy as np


class TestHeatwaveFrequency:
    def test_heatwave_frequency_with_breaks_null_case(self):
        hot_day_null = np.zeros(100, dtype=int)
        season_range = np.array([[0, 100]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_null, season_range), np.array([0]))

    def test_heatwave_frequency_with_breaks_full_case(self):
        hot_day_full = np.ones(100, dtype=bool)
        season_range = np.array([[0, 100]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_full, season_range), np.array([100]))

    def test_heatwave_frequency_with_breaks_case1(self):
        hot_day_case1 = np.array(
            [0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0],
            dtype=int)
        season_range = np.array([[0, hot_day_case1.size]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_case1, season_range), np.array([12]))

    def test_heatwave_frequency_with_breaks_case2(self):
        hot_day_case2 = np.array(
            [0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 3],
            dtype=int)
        season_range = np.array([[0, hot_day_case2.size]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_case2, season_range), np.array([12]))

    def test_heatwave_frequency_with_breaks_case3(self):
        hot_day_case3 = np.array(
            [0, 0, 0, 1, 1, 0, 2, 0, 3, 0, 0, 0, 0, 4, 4, 4, 0, 0, 0, 0],
            dtype=int)
        season_range = np.array([[0, hot_day_case3.size]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_case3, season_range), np.array([7]))

    def test_heatwave_frequency_with_breaks_season_full_case(self):
        hot_day_full = np.ones(100, dtype=bool)
        season_range = np.array([[0, 5], [0, 10], [20, 30], [42, 50]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_full, season_range), np.array([5, 10, 10, 8]))

    def test_heatwave_frequency_with_breaks_season_case1(self):
        hot_day_case3 = np.array(
            [0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0],
            dtype=int)
        season_range = np.array([[0, 8], [8, hot_day_case3.size]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_case3, season_range), np.array([7, 5]))

    def test_heatwave_frequency_with_breaks_season_case2(self):
        hot_day_case3 = np.array(
            [0, 0, 0, 1, 1, 0, 2, 0, 3, 0, 0, 0, 0, 4, 4, 4, 0, 0, 0, 0],
            dtype=int)
        season_range = np.array([[0, 8], [8, hot_day_case3.size]], dtype=int)
        assert np.array_equal(heat_stats.heatwave_frequency_with_breaks(hot_day_case3, season_range), np.array([3, 4]))
