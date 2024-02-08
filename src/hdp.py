#!/usr/bin/env python
"""
hdp.py

Heatwave Diagnostics Package (HDP)

Contains primary functions for computing heatwave thresholds and metrics using numpy with xarray wrapper functions.

Developer: Cameron Cummins
Contact: cameron.cummins@utexas.edu
2/8/24
"""
import xarray
import numpy as np
from numba import jit
from datetime import datetime
from scipy import stats


def compute_threshold(temperature_dataset: xarray.DataArray, percentiles: np.ndarray, temp_path: str="No path provided.") -> xarray.DataArray:
    """
    Computes day-of-year quantile temperatures for given temperature dataset and percentile. The output is used as the threshold input for 'heatwave_metrics.py'.
    
    Keyword arguments:
    temperature_data -- Temperature dataset to compute quantiles from
    percentile -- Percentile to compute the quantile temperatures at
    temp_path -- Path to 'temperature_data' temperature dataset to add to meta-data
    """
    
    window_samples = datetimes_to_windows(temperature_dataset.time.values, 7)
    annual_threshold = compute_percentile_thresholds(temperature_dataset.values, window_samples, percentiles)
    
    return xarray.Dataset(
        data_vars=dict(
            threshold=(["percentile", "day", "lat", "lon"], annual_threshold),
        ),
        coords=dict(
            lon=(["lon"], temperature_dataset.lon.values),
            lat=(["lat"], temperature_dataset.lat.values),
            day=np.arange(0, num_days),
            percentile=percentiles
        ),
        attrs={
            "description": f"Percentile temperatures.",
            "percentiles": str(percentile),
            "temperature dataset path": temp_path
        },
    )

def compute_metrics(temp_ds: xarray.DataArray, control_threshold: xarray.DataArray, temp_path: str="No path provided.", control_path: str="No path provided.") -> xarray.Dataset:
    """
    Computes the relevant heatwave metrics for a given temperature dataset and threshold.
    
    Keyword arguments:
    temp_ds -- Temperature dataset to compare against threshold and compute heatwave metrics for
    control_threshold -- Day-of-year temperature dataset to use as threshold for heatwave days
    temp_path -- Path to 'temp_ds' temperature dataset to add to meta-data
    control_path -- Path to 'control_threshold' threshold temperature dataset to add to meta-data
    """
    hot_days = indicate_hot_days(temp_ds, control_threshold)
    indexed_heatwaves = np.zeros(hot_days.shape, dtype=np.short)

    for i in range(hot_days.shape[1]):
        for j in range(hot_days.shape[2]):
            indexed_heatwaves[:, i, j] = index_heatwaves(hot_days[:, i, j])

    num_index_heatwaves = indexed_heatwaves > 0
    years = temp_ds.time.values[-1].year - temp_ds.time.values[0].year + 1

    south_hemisphere = np.ones((int(temp_ds.shape[1]/2), temp_ds.shape[2]), dtype=int)
    south_hemisphere.resize((temp_ds.shape[1], temp_ds.shape[2]))
    north_hemisphere = 1 - south_hemisphere
    
    hwf = np.zeros((years, indexed_heatwaves.shape[1], indexed_heatwaves.shape[2]), dtype=int)
    hwd = np.zeros((years, indexed_heatwaves.shape[1], indexed_heatwaves.shape[2]), dtype=int)
    for index in range(0, years):
        north_lower, north_upper = (365*index + 121, 365*index + 274)
        south_lower, south_upper = (365*index + 304, 365*index + 455)
        
        hwf[index] = north_hemisphere*np.sum(num_index_heatwaves[north_lower:north_upper], axis=0) + south_hemisphere*np.sum(num_index_heatwaves[south_lower:south_upper], axis=0)
        
        north_hw_indices = indexed_heatwaves[north_lower:north_upper]
        south_hw_indices = indexed_heatwaves[south_lower:south_upper]
        
        masked_north = north_hw_indices.astype(np.float16)
        masked_north[north_hw_indices == 0] = np.nan

        masked_south = south_hw_indices.astype(np.float16)
        masked_south[south_hw_indices == 0] = np.nan

        hwd[index] = north_hemisphere*np.sum((north_hw_indices == stats.mode(masked_north, axis=0, nan_policy="omit")[0].astype(np.short)), axis=0) + south_hemisphere*np.sum((masked_south == stats.mode(south_hw_indices, axis=0, nan_policy="omit")[0].astype(np.short)), axis=0)

    meta = {
            "temperature dataset path": temp_path,
            "control dataset path": control_path,
            "time_created": str(datetime.now()),
            "author": "Cameron Cummins",
            "credit": "Original algorithm written by Tammas Loughran and modified by Jane Baldwin",
            "Tammas Loughran's repository": "https://github.com/tammasloughran/ehfheatwaves",
            "script repository": "https://github.austin.utexas.edu/csc3323/heatwave_analysis_package",
            "contact": "cameron.cummins@utexas.edu"
    }
    for key in control_threshold.attrs:
        meta[f"threshold-{key}"] = control_threshold.attrs[key]

    return xarray.Dataset(
        data_vars=dict(
            HWF=(["year", "lat", "lon"], hwf),
            HWD=(["year", "lat", "lon"], hwd)
        ),
        coords=dict(
            lon=(["lon"], temp_ds.lon.values),
            lat=(["lat"], temp_ds.lat.values),
            year=np.arange(temp_ds.time.values[0].year, temp_ds.time.values[-1].year+1),
        ),
        attrs=meta,
        )

