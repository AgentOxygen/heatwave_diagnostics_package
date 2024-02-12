#!/usr/bin/env python
"""
heat_core.py

Contains core functions for analyzing timeseries data. 
All methods are static. The 'HeatCore' class serves as a library for hdp.py

Parallelism is enabled by default.

Developer: Cameron Cummins
Contact: cameron.cummins@utexas.edu
2/8/24
"""
from numba import njit, prange
import numba as nb
import numpy as np


class HeatCore:
    @staticmethod
    def get_range_indices(times: np.array, start: tuple, end: tuple):
        num_years = times[-1].year - times[0].year + 1
        ranges = np.zeros((num_years, 2), dtype=int) - 1

        n = 0
        looking_for_start = True
        for t in range(times.shape[0]):
            if looking_for_start:
                if times[t].month == start[0] and times[t].day == start[1]:
                    looking_for_start = False
                    ranges[n, 0] = t
            else:
                if times[t].month == end[0] and times[t].day == end[1]:
                    looking_for_start = True
                    ranges[n, 1] = t
                    n += 1

        if not looking_for_start:
            ranges[-1, -1] = times.shape[0]

        return ranges

    
    @staticmethod
    def compute_hemisphere_ranges(temperatures: xarray.DataArray):
        north_ranges = get_range_indices(temperatures.time.values, (5, 1), (10, 1))
        south_ranges = get_range_indices(temperatures.time.values, (10, 1), (3, 1))

        ranges = np.zeros((north_ranges.shape[0], 2, temperatures.shape[1], temperatures.shape[2]), dtype=int) - 1

        for i in range(temperatures.shape[1]):
            for j in range(temperatures.shape[2]):
                if i < ranges.shape[2] / 2:
                    ranges[:, :, i, j] = south_ranges
                else:
                    ranges[:, :, i, j] = north_ranges

        return ranges
    
    
    @staticmethod
    @njit(parallel=True)
    def compute_int64_spatial_func(ts_spatial_array, func):
        results = np.zeros(ts_spatial_array.shape, nb.int64)

        for i in prange(ts_spatial_array.shape[1]):
            for j in prange(ts_spatial_array.shape[2]):
                results[:, i, j] = func(ts_spatial_array[:, i, j])
        return results

    
    @staticmethod
    @njit(parallel=True)
    def indicate_hot_days(temperatures: np.ndarray, threshold: np.ndarray, doy_map: np.ndarray) -> np.ndarray:
        hot_days = np.zeros(temperatures.shape, dtype=nb.boolean)

        for time_index in prange(temperatures.shape[0]):
            if doy_map[time_index] >= 0:
                hot_days[time_index] = temperatures[time_index] > threshold[doy_map[time_index]]
        return hot_days
    
    
    @staticmethod
    def datetimes_to_windows(datetimes: np.ndarray, window_radius: int=7) -> np.ndarray:
        """
        Calculates sample windows for array indices from the datetime dimension 

        datetimes - array of datetime objects corresponding to the dataset's time dimension
        window_radius - radius of windows to generate
        """
        day_of_yr_to_index = {}
        for index, date in enumerate(datetimes):
            if date.dayofyr in day_of_yr_to_index.keys(): 
                day_of_yr_to_index[date.dayofyr].append(index)
            else:
                day_of_yr_to_index[date.dayofyr] = [index]

        time_index = np.zeros((len(day_of_yr_to_index), np.max([len(x) for x in day_of_yr_to_index.values()])), int) - 1

        for index, day_of_yr in enumerate(day_of_yr_to_index):
            for i in range(len(day_of_yr_to_index[day_of_yr])):
                time_index[index, i] = day_of_yr_to_index[day_of_yr][i]

        window_samples = np.zeros((len(day_of_yr_to_index), 2*window_radius+1, time_index.shape[1]), int)

        for day_of_yr in range(window_samples.shape[0]):
            for window_index in range(window_samples.shape[1]):
                sample_index = day_of_yr + window_radius - window_index            
                if sample_index >= time_index.shape[0]:
                    sample_index = time_index.shape[0] - sample_index
                window_samples[day_of_yr, window_index] = time_index[sample_index]
        return window_samples.reshape((window_samples.shape[0], window_samples.shape[1]*window_samples.shape[2]))


    @staticmethod
    @njit(parallel=True)
    def compute_percentiles(temp_data, window_samples, percentiles):
        """
        Computes the temperatures for multiple percentiles using sample index windows.

        temp_data - dataset containing temperatures to compute percentiles from
        window_samples - array containing "windows" of indices cenetered at each day of the year
        percentiles - array of perecentiles to compute [0, 1]
        """
        percentile_temp = np.zeros((percentiles.shape[0], window_samples.shape[0], temp_data.shape[1], temp_data.shape[2]), np.float32)

        for doy_index in prange(window_samples.shape[0]):
            sample_time_indices = window_samples[doy_index]

            time_index_size = 0
            for sample_time_index in prange(sample_time_indices.shape[0]):
                if sample_time_indices[sample_time_index] != -1:
                    time_index_size += 1

            temp_sample = np.zeros((time_index_size, temp_data.shape[1], temp_data.shape[2]), np.float32)

            time_index = 0
            for sample_time_index in prange(sample_time_indices.shape[0]):
                if sample_time_indices[sample_time_index] != -1:
                    temp_sample[time_index] = temp_data[sample_time_indices[sample_time_index]]
                    time_index += 1

            for i in prange(temp_sample.shape[1]):
                for j in prange(temp_sample.shape[2]):
                    percentile_temp[:, doy_index, i, j] = np.quantile(temp_sample[:, i, j], percentiles)
        return percentile_temp
