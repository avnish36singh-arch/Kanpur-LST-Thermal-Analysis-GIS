#!/usr/bin/env python3
"""
Kanpur Urban Heat Island (UHI) Thermal Analysis via Google Earth Engine (GEE)
Cloud-native satellite observation using Landsat 8 and Landsat 9 Collection 2 Level-2 Surface Temperature.

Key Highlights:
- Zero local downloads / zero QGIS dependencies required.
- Standard USGS Landsat C2 L2 Surface Temperature formula: ST (K) = DN * 0.00341802 + 149.0
- Concentric annular gradient zones: Core (0-5 km), Suburban (5-15 km ring), Rural (15-20 km ring)
- Cross-validation against coarse MERRA-2 daily grid data from NASA POWER
- Generates publication plots and CSV export
"""

import os
import sys
import argparse
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import ee
except ImportError:
    print("[ERROR] Google Earth Engine Python API is not installed.")
    print("Please install via: pip install earthengine-api google-auth-oauthlib")
    sys.exit(1)


def initialize_earth_engine(project_id=None):
    """
    Initializes the Google Earth Engine API with authentication checking.
    """
    try:
        if project_id:
            ee.Initialize(project=project_id)
            print(f"[OK] Earth Engine initialized successfully with project: {project_id}")
        else:
            ee.Initialize()
            print("[OK] Earth Engine initialized successfully.")
    except Exception as exc:
        print("\n" + "=" * 70)
        print("[!] Google Earth Engine Authentication Required")
        print("=" * 70)
        print(f"Details: {exc}\n")
        print("To authenticate your account, run this command in your VSCode terminal:")
        print("    earthengine authenticate")
        print("\nOr in interactive Python:")
        print("    import ee; ee.Authenticate()")
        print("\nIf you are using Google Cloud with a specific Project ID, run:")
        print("    python kanpur_uhi_analysis.py --project your-google-cloud-project-id")
        print("=" * 70 + "\n")
        sys.exit(1)


def get_kanpur_geometries(lat=26.4499, lon=80.3319, use_annular_rings=True):
    """
    Constructs Kanpur urban center point, 20km analysis boundary,
    and concentric microclimate zones (Core, Suburban, Rural).
    """
    kanpur_center = ee.Geometry.Point([lon, lat])
    kanpur_buffer = kanpur_center.buffer(20000)  # 20 km total radius

    # Core buffer: 0 - 5 km
    core_zone = kanpur_center.buffer(5000)

    if use_annular_rings:
        # Annular rings isolate the microclimate gradient without overlapping the core
        suburban_zone = kanpur_center.buffer(15000).difference(core_zone)
        rural_zone = kanpur_center.buffer(20000).difference(kanpur_center.buffer(15000))
    else:
        # Cumulative circular buffers
        suburban_zone = kanpur_center.buffer(15000)
        rural_zone = kanpur_center.buffer(20000)

    return kanpur_center, kanpur_buffer, core_zone, suburban_zone, rural_zone


def load_landsat_surface_temp(roi, start_date='2021-07-01', end_date='2022-10-31', max_cloud_cover=10):
    """
    Queries Landsat 8 and Landsat 9 Collection 2 Tier 1 Level-2 surface temperature products.
    Converts Digital Numbers (DN) to degrees Celsius using the USGS formula:
        Kelvin = DN * 0.00341802 + 149.0
        Celsius = Kelvin - 273.15 = DN * 0.00341802 - 124.15
    """
    # Landsat 9 C2 L2
    l9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover))

    # Landsat 8 C2 L2
    l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover))

    # Merge collections to provide robust coverage across all seasons
    combined = l9.merge(l8).sort('system:time_start')

    total_scenes = combined.size().getInfo()
    print(f"[INFO] Found {total_scenes} cloud-free Landsat 8/9 scenes (Cloud Cover < {max_cloud_cover}%)")

    def convert_celsius(img):
        # USGS Landsat Collection 2 Level 2 Surface Temperature conversion:
        # ST_B10 is uint16 with scale 0.00341802 and offset 149.0 (Kelvin)
        lst_celsius = img.select('ST_B10') \
            .multiply(0.00341802) \
            .add(149.0) \
            .subtract(273.15) \
            .rename('LST_Celsius')

        return img.addBands(lst_celsius).copyProperties(img, ['system:time_start', 'CLOUD_COVER'])

    return combined.map(convert_celsius), total_scenes


def load_local_merra2_benchmark(csv_path="data/raw/kanpur_nasa_power_daily.csv"):
    """
    Loads daily MERRA-2 reanalysis data for Kanpur from local NASA POWER dataset if available.
    """
    if os.path.exists(csv_path):
        df_merra = pd.read_csv(csv_path)
        if 'Date' in df_merra.columns and 'LST_Skin_C' in df_merra.columns:
            return df_merra.set_index('Date')['LST_Skin_C'].to_dict()
    return {}


def run_kanpur_uhi_analysis(project_id=None,
                            start_date='2021-07-01',
                            end_date='2022-10-31',
                            max_scenes=10,
                            max_cloud_cover=10,
                            clip_admin=False,
                            output_dir="."):
    """
    Executes the Kanpur Urban Heat Island workflow:
    1. Authenticates & initializes Earth Engine
    2. Clips / filters Landsat 8/9 thermal collection
    3. Computes Core, Suburban, and Rural zone means
    4. Evaluates UHI intensity
    5. Benchmarks against coarse MERRA-2
    6. Produces publication plots and CSV report
    """
    os.makedirs(output_dir, exist_ok=True)
    initialize_earth_engine(project_id)

    print("\n--- Initializing Kanpur Spatial Geometries ---")
    kanpur_center, kanpur_buffer, core_zone, suburban_zone, rural_zone = get_kanpur_geometries()

    # Optional boundary clipping with FAO GAUL Kanpur Nagar
    if clip_admin:
        try:
            print("[INFO] Applying FAO GAUL Kanpur Nagar administrative clipping...")
            urban_admin = ee.FeatureCollection("FAO/GAUL/2015/level2") \
                .filter(ee.Filter.eq('ADM2_NAME', 'Kanpur Nagar'))
            analysis_geom = urban_admin.geometry()
        except Exception as e:
            print(f"[WARN] Could not fetch administrative boundary: {e}. Using 20km circular buffer.")
            analysis_geom = kanpur_buffer
    else:
        analysis_geom = kanpur_buffer

    # Load Landsat surface temperature
    thermal_col, total_scenes = load_landsat_surface_temp(
        roi=analysis_geom,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover
    )

    if total_scenes == 0:
        print("[WARN] No scenes found within the specified date range and cloud cover threshold.")
        print("Try expanding --start-date, --end-date, or increasing --cloud-cover.")
        return None

    # Load local MERRA-2 lookup for direct ground-truth comparison
    merra2_lookup = load_local_merra2_benchmark()

    # Process scenes
    scenes_to_process = min(total_scenes, max_scenes)
    scene_list = thermal_col.toList(scenes_to_process)

    print(f"\nProcessing {scenes_to_process} Landsat thermal scenes across Kanpur zones...")
    print(f"{'Date':<12} | {'Core (0-5km)':<14} | {'Suburban (5-15km)':<18} | {'Rural (15-20km)':<16} | {'UHI (Core-Rural)':<16} | {'MERRA-2 (50km)'}")
    print("-" * 95)

    dates = []
    results_core = []
    results_suburban = []
    results_rural = []
    merra2_matched = []

    for i in range(scenes_to_process):
        img = ee.Image(scene_list.get(i))
        lst_band = img.select('LST_Celsius')

        # Extract capture date
        date_ms = img.get('system:time_start').getInfo()
        date_dt = datetime.fromtimestamp(date_ms / 1000, tz=timezone.utc)
        date_str = date_dt.strftime('%Y-%m-%d')

        # Reduce regions to calculate spatial mean temperatures (°C)
        core_stat = lst_band.reduceRegion(reducer=ee.Reducer.mean(), geometry=core_zone, scale=30, maxPixels=1e9).getInfo()
        suburban_stat = lst_band.reduceRegion(reducer=ee.Reducer.mean(), geometry=suburban_zone, scale=30, maxPixels=1e9).getInfo()
        rural_stat = lst_band.reduceRegion(reducer=ee.Reducer.mean(), geometry=rural_zone, scale=30, maxPixels=1e9).getInfo()

        core_temp = core_stat.get('LST_Celsius')
        suburban_temp = suburban_stat.get('LST_Celsius')
        rural_temp = rural_stat.get('LST_Celsius')

        if core_temp is not None and suburban_temp is not None and rural_temp is not None:
            uhi_scene = core_temp - rural_temp
            merra_val = merra2_lookup.get(date_str, np.nan)
            merra_display = f"{merra_val:.2f}°C" if not np.isnan(merra_val) else "N/A"

            dates.append(date_str)
            results_core.append(core_temp)
            results_suburban.append(suburban_temp)
            results_rural.append(rural_temp)
            merra2_matched.append(merra_val)

            print(f"{date_str:<12} | {core_temp:>10.2f}°C   | {suburban_temp:>14.2f}°C   | {rural_temp:>12.2f}°C   | {uhi_scene:>12.2f}°C   | {merra_display}")

    if not dates:
        print("[ERROR] No valid scene temperatures could be extracted.")
        return None

    # Compute overall UHI statistics
    mean_core = float(np.mean(results_core))
    mean_suburban = float(np.mean(results_suburban))
    mean_rural = float(np.mean(results_rural))
    uhi_intensity = mean_core - mean_rural

    print("\n" + "=" * 55)
    print("           KANPUR UHI ANALYSIS RESULTS SUMMARY")
    print("=" * 55)
    print(f"Processed Scenes     : {len(dates)} cloud-free satellite acquisitions")
    print(f"Date Span            : {dates[0]} to {dates[-1]}")
    print(f"Urban Core Mean (0-5km)    : {mean_core:6.2f} °C")
    print(f"Suburban Mean (5-15km)     : {mean_suburban:6.2f} °C")
    print(f"Rural Mean (15-20km)       : {mean_rural:6.2f} °C")
    print(f"Urban Heat Island (UHI) ΔT : {uhi_intensity:+6.2f} °C (Core - Rural)")

    valid_merra = [v for v in merra2_matched if not np.isnan(v)]
    if valid_merra:
        merra_avg = np.mean(valid_merra)
        print(f"MERRA-2 Grid Reanalysis Avg: {merra_avg:6.2f} °C (50 km coarse cell)")
        print(f"Core Resolution Gain (LST-MERRA): {mean_core - merra_avg:+6.2f} °C")
    print("=" * 55 + "\n")

    # Export to CSV
    csv_file = os.path.join(output_dir, 'kanpur_uhi_results.csv')
    df_results = pd.DataFrame({
        'date': dates,
        'core_temp_c': np.round(results_core, 2),
        'suburban_temp_c': np.round(results_suburban, 2),
        'rural_temp_c': np.round(results_rural, 2),
        'uhi_intensity_c': np.round(np.array(results_core) - np.array(results_rural), 2),
        'merra2_skin_temp_c': np.round(merra2_matched, 2)
    })
    df_results.to_csv(csv_file, index=False)
    print(f"[OK] Saved CSV dataset: {csv_file}")

    # ============ PLOT 1: TIME SERIES ============
    plt.figure(figsize=(11, 5.5), dpi=150)
    plt.plot(dates, results_core, marker='o', linewidth=2, color='#d62728', label='Urban Core (0–5 km)')
    plt.plot(dates, results_suburban, marker='s', linewidth=1.8, color='#ff7f0e', label='Suburban Ring (5–15 km)')
    plt.plot(dates, results_rural, marker='^', linewidth=1.8, color='#2ca02c', label='Rural Ring (15–20 km)')

    if any(not np.isnan(v) for v in merra2_matched):
        plt.plot(dates, merra2_matched, marker='D', linestyle='--', color='#1f77b4', alpha=0.8,
                 label='Coarse MERRA-2 Reanalysis (50 km)')

    plt.xlabel('Satellite Acquisition Date', fontsize=11, fontweight='bold', labelpad=8)
    plt.ylabel('Land Surface Temperature (°C)', fontsize=11, fontweight='bold', labelpad=8)
    plt.title(f'Kanpur Urban Heat Island: Landsat 8/9 Cloud Thermal Time Series\nMean UHI Intensity = +{uhi_intensity:.2f}°C',
              fontsize=12, fontweight='bold', pad=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, loc='best')
    plt.xticks(rotation=40, ha='right', fontsize=9)
    plt.tight_layout()
    timeseries_path = os.path.join(output_dir, 'kanpur_uhi_timeseries.png')
    plt.savefig(timeseries_path, dpi=150)
    plt.close()
    print(f"[OK] Saved Time Series Plot: {timeseries_path}")

    # ============ PLOT 2: ZONE BAR CHART ============
    zones = ['Urban Core\n(0–5 km)', 'Suburban\n(5–15 km)', 'Rural\n(15–20 km)']
    temps = [mean_core, mean_suburban, mean_rural]
    colors = ['#d9383a', '#f58231', '#3cb44b']

    plt.figure(figsize=(7.5, 5.5), dpi=150)
    bars = plt.bar(zones, temps, color=colors, alpha=0.85, edgecolor='black', width=0.55)
    plt.ylabel('Mean Surface Temperature (°C)', fontsize=11, fontweight='bold', labelpad=8)
    plt.title(f'Kanpur Concentric Thermal Profile\nUHI Intensity (Core - Rural) = +{uhi_intensity:.2f}°C',
              fontsize=12, fontweight='bold', pad=12)
    
    y_min = max(0, min(temps) - 4)
    y_max = max(temps) + 4
    plt.ylim([y_min, y_max])
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # Add numeric labels on bars
    for bar, temp in zip(bars, temps):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                 f'{temp:.2f}°C', ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Annotate difference arrow
    plt.annotate(
        f'ΔT = +{uhi_intensity:.2f}°C',
        xy=(2, mean_rural), xytext=(0, mean_core),
        arrowprops=dict(arrowstyle="<->", color="black", lw=1.5, ls="--"),
        fontweight='bold', color='#900C3F', ha='center'
    )

    plt.tight_layout()
    zones_path = os.path.join(output_dir, 'kanpur_uhi_zones.png')
    plt.savefig(zones_path, dpi=150)
    plt.close()
    print(f"[OK] Saved Zones Comparison Plot: {zones_path}")

    return {
        'dates': dates,
        'mean_core': mean_core,
        'mean_suburban': mean_suburban,
        'mean_rural': mean_rural,
        'uhi_intensity': uhi_intensity,
        'csv_file': csv_file,
        'timeseries_plot': timeseries_path,
        'zones_plot': zones_path
    }


def main():
    parser = argparse.ArgumentParser(description="Kanpur Urban Heat Island (UHI) Thermal Analysis via Google Earth Engine")
    parser.add_argument('--project', type=str, default=None, help="Google Cloud Project ID for Earth Engine")
    parser.add_argument('--start-date', type=str, default='2021-07-01', help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end-date', type=str, default='2022-10-31', help="End date (YYYY-MM-DD)")
    parser.add_argument('--max-scenes', type=int, default=10, help="Maximum number of scenes to process")
    parser.add_argument('--cloud-cover', type=int, default=10, help="Maximum cloud cover percentage")
    parser.add_argument('--clip-admin', action='store_true', help="Clip analysis to Kanpur Nagar administrative boundary")
    parser.add_argument('--output-dir', type=str, default='.', help="Directory to save output plots and CSV")

    args = parser.parse_args()

    run_kanpur_uhi_analysis(
        project_id=args.project,
        start_date=args.start_date,
        end_date=args.end_date,
        max_scenes=args.max_scenes,
        max_cloud_cover=args.cloud_cover,
        clip_admin=args.clip_admin,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
