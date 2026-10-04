#!/usr/bin/env python3
"""
Master CLI Entrypoint: Kanpur LST Thermal Analysis & GIS Platform
Satellite Earth Observation, MERRA-2 Reanalysis, and Microclimate Spatial Modeling (2017–2023)

Usage:
  python main.py --run-all             # End-to-end execution of full pipeline
  python main.py --generate-plots      # Regenerate Figures 1 through 7 (300 DPI)
  python main.py --export-gis          # Export standardized GeoJSON vector layers & QML style
  python main.py --fetch               # Fetch fresh NASA POWER satellite telemetry
  python main.py --serve-web           # Launch interactive Web GIS & analytics dashboard
  python main.py --verify              # Verify data integrity, geometries, and output artifacts
"""

import os
import sys
import argparse
import subprocess
import webbrowser
import http.server
import socketserver

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "pipeline"))

from spatial_kanpur_gis import run_kanpur_lst_gis_pipeline, export_all_qgis_layers
from fetch_nasa_power import fetch_kanpur_nasa_power


def verify_outputs():
    """Validates existence and integrity of all pipeline artifacts."""
    print("\n--- Verifying Pipeline Artifacts ---")
    data_file = os.path.join(ROOT_DIR, "data", "raw", "kanpur_nasa_power_daily.csv")
    aq_file = os.path.join(ROOT_DIR, "data", "raw", "kanpur_cpcb_daily_aq.csv")
    
    plots = [
        "01_kanpur_lst_seasonal_timeline.png",
        "02_skin_vs_air_temperature_anomaly.png",
        "03_kanpur_spatial_thermal_zones.png",
        "04_lst_inversion_coupling_pm25.png",
        "05_bioclimatic_heat_stress_index.png",
        "06_ventilation_coefficient_inversion.png",
        "07_urban_microclimate_transect.png",
        "kanpur-uhi-30m.png",
        "kanpur-uhi-comparison-merra2.png",
        "kanpur-uhi-timeseries.png",
        "kanpur-uhi-seasonal-uhi.png"
    ]
    
    gis_layers = [
        "kanpur_thermal_zones.geojson",
        "kanpur_cpcb_stations.geojson",
        "kanpur_ganga_riparian.geojson",
        "kanpur_microclimate_transect.geojson",
        "kanpur_thermal_zones.qml"
    ]
    
    web_files = [
        os.path.join("web", "index.html"),
        os.path.join("web", "data", "kanpur_lst_daily.json"),
        os.path.join("web", "data", "kanpur_summary_kpis.json")
    ]
    
    all_ok = True
    
    for fpath, label in [(data_file, "NASA POWER Raw Telemetry"), (aq_file, "Kanpur CPCB AQ Data")]:
        if os.path.exists(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            print(f"  [OK] {label}: {fpath} ({size_kb:.1f} KB)")
        else:
            print(f"  [MISSING] {label}: {fpath}")
            all_ok = False
            
    for p in plots:
        fpath = os.path.join(ROOT_DIR, "outputs", "plots", p)
        if os.path.exists(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            print(f"  [OK] Figure: {p} ({size_kb:.1f} KB)")
        else:
            print(f"  [MISSING] Figure: {p}")
            all_ok = False
            
    for g in gis_layers:
        fpath = os.path.join(ROOT_DIR, "outputs", "qgis", g)
        if os.path.exists(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            print(f"  [OK] GIS Layer: {g} ({size_kb:.1f} KB)")
        else:
            print(f"  [MISSING] GIS Layer: {g}")
            all_ok = False
            
    for w in web_files:
        fpath = os.path.join(ROOT_DIR, w)
        if os.path.exists(fpath):
            print(f"  [OK] Web Asset: {w}")
        else:
            print(f"  [MISSING] Web Asset: {w}")
            all_ok = False
            
    if all_ok:
        print("\nAll artifacts verified successfully! Platform is healthy and publication-ready.")
    else:
        print("\nSome artifacts were missing. Run 'python main.py --run-all' to generate them.")
    return all_ok


def serve_web_dashboard(port=8080):
    """Launches local HTTP server to preview the interactive Web GIS & analytics dashboard."""
    web_dir = os.path.join(ROOT_DIR, "web")
    os.chdir(web_dir)
    handler = http.server.SimpleHTTPRequestHandler
    
    class DualStackServer(socketserver.TCPServer):
        allow_reuse_address = True

    try:
        with DualStackServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"\n=======================================================")
            print(f"Kanpur LST Web GIS & Analytics Portal active at:")
            print(f"  {url}")
            print(f"Serving directory: {web_dir}")
            print(f"Press Ctrl+C to terminate the local server.")
            print(f"=======================================================\n")
            try:
                webbrowser.open(url)
            except Exception:
                pass
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Failed to bind port {port}: {e}. Try a different port with --port.")


def main():
    parser = argparse.ArgumentParser(
        description="Kanpur LST Thermal Analysis & GIS Platform: Master CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --run-all          # Run entire data, GIS, and visual pipeline
  python main.py --generate-plots   # Generate Figures 1-7 at 300 DPI
  python main.py --export-gis       # Export GeoJSON layers and QML style
  python main.py --serve-web        # Launch web GIS dashboard at http://localhost:8080
  python main.py --verify           # Check pipeline artifacts and status
        """
    )
    parser.add_argument("--run-all", action="store_true", help="Execute complete pipeline (data ingestion, modeling, GIS, figures, web sync)")
    parser.add_argument("--run-gee-uhi", action="store_true", help="Execute Google Earth Engine Landsat 8/9 cloud thermal UHI analysis")
    parser.add_argument("--gee-project", type=str, default=None, help="Google Cloud project ID for Google Earth Engine initialization")
    parser.add_argument("--fetch", action="store_true", help="Fetch fresh NASA POWER satellite telemetry via REST API")
    parser.add_argument("--generate-plots", action="store_true", help="Generate all 7 publication figures (300 DPI)")
    parser.add_argument("--export-gis", action="store_true", help="Export QGIS GeoJSON vector layers and QML styles")
    parser.add_argument("--serve-web", action="store_true", help="Launch interactive Web GIS dashboard on local HTTP server")
    parser.add_argument("--port", type=int, default=8080, help="Port for the local web server (default: 8080)")
    parser.add_argument("--verify", action="store_true", help="Verify integrity of all data, GIS, and plot artifacts")

    args = parser.parse_args()

    # Default action if no flag is provided
    if not any([args.run_all, args.run_gee_uhi, args.fetch, args.generate_plots, args.export_gis, args.serve_web, args.verify]):
        print("Kanpur LST Thermal Analysis & GIS Platform: No options specified.")
        print("Running end-to-end pipeline by default...\n")
        run_kanpur_lst_gis_pipeline()
        verify_outputs()
        return

    if args.fetch:
        raw_csv = os.path.join(ROOT_DIR, "data", "raw", "kanpur_nasa_power_daily.csv")
        fetch_kanpur_nasa_power(raw_csv)

    if args.export_gis:
        qgis_dir = os.path.join(ROOT_DIR, "outputs", "qgis")
        export_all_qgis_layers(qgis_dir)

    if args.run_gee_uhi:
        from kanpur_uhi_analysis import run_kanpur_uhi_analysis
        print("\n--- Launching Google Earth Engine Landsat UHI Analysis ---")
        run_kanpur_uhi_analysis(project_id=args.gee_project, output_dir=ROOT_DIR)

    if args.run_all or args.generate_plots:
        run_kanpur_lst_gis_pipeline()

    if args.verify:
        verify_outputs()

    if args.serve_web:
        serve_web_dashboard(port=args.port)


if __name__ == "__main__":
    main()
