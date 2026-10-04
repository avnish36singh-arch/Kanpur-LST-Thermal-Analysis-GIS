"""
Unit tests for data pipeline and thermodynamic modeling metrics.
Compatible with standard library unittest and pytest.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "pipeline"))

from thermal_metrics import (
    compute_heat_index_celsius,
    categorize_heat_index,
    estimate_boundary_layer_height,
    compute_ventilation_coefficient,
    categorize_ventilation,
    compute_nocturnal_inversion_severity_index,
    categorize_nisi,
    enrich_thermal_dataset
)


class TestThermalPipeline(unittest.TestCase):

    def test_heat_index_calculation(self):
        # Below 20°C returns air temp
        self.assertEqual(compute_heat_index_celsius(15.0, 60.0), 15.0)

        # Typical hot humid day: 35°C and 70% RH produces high apparent temperature
        hi = compute_heat_index_celsius(35.0, 70.0)
        self.assertGreater(hi, 45.0)
        self.assertIn(categorize_heat_index(hi), ["Danger", "Extreme Danger"])

        # Safe temperature
        self.assertEqual(categorize_heat_index(24.0), "Normal / Safe")

    def test_boundary_layer_height_proxy(self):
        # Radiative cooling inversion (Delta T < 0): shallow PBLH
        pblh_inv = estimate_boundary_layer_height(delta_t=-2.0, solar_radiation=80.0, wind_speed=1.5)
        self.assertTrue(150.0 <= pblh_inv <= 600.0)

        # Solar convective heating (Delta T > 0): deep PBLH
        pblh_conv = estimate_boundary_layer_height(delta_t=+2.5, solar_radiation=250.0, wind_speed=3.0)
        self.assertGreaterEqual(pblh_conv, 1200.0)
        self.assertGreater(pblh_conv, pblh_inv)

    def test_ventilation_coefficient(self):
        vc_low = compute_ventilation_coefficient(pblh_m=250.0, wind_speed_mps=1.2)
        self.assertLess(vc_low, 1000.0)
        self.assertEqual(categorize_ventilation(vc_low), "Severe Stagnation")

        vc_high = compute_ventilation_coefficient(pblh_m=2000.0, wind_speed_mps=4.0)
        self.assertGreaterEqual(vc_high, 6000.0)
        self.assertEqual(categorize_ventilation(vc_high), "Good Dispersion")

    def test_nocturnal_inversion_severity_index(self):
        # Convective daytime (Delta T > 0)
        self.assertEqual(compute_nocturnal_inversion_severity_index(delta_t=1.5, rh_pct=40.0, wind_speed=3.0), 0.0)
        self.assertEqual(categorize_nisi(0.0), "Convective / Mixing")

        # Severe winter inversion (Delta T = -2.5°C, high humidity, low wind)
        nisi_severe = compute_nocturnal_inversion_severity_index(delta_t=-2.5, rh_pct=85.0, wind_speed=1.0)
        self.assertGreater(nisi_severe, 1.8)
        self.assertEqual(categorize_nisi(nisi_severe), "Severe Inversion Trap")

    def test_nasa_power_data_integrity(self):
        csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "kanpur_nasa_power_daily.csv")
        self.assertTrue(os.path.exists(csv_path), "NASA POWER data file is missing")

        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 2556, f"Expected 2,556 daily records (2017-2023), got {len(df)}")

        required_cols = [
            "Date", "Year", "Month", "Day", "Season",
            "LST_Skin_C", "Air_Temp_2M_C", "Temp_Max_2M_C", "Temp_Min_2M_C",
            "Delta_T_Skin_Air_C", "Solar_Radiation_MJ_m2", "Relative_Humidity_Pct", "Wind_Speed_2M_mps"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

        self.assertGreater(df["LST_Skin_C"].notna().sum(), 2500)
        self.assertTrue(5.0 <= df["LST_Skin_C"].min() <= 10.0)
        self.assertTrue(40.0 <= df["LST_Skin_C"].max() <= 50.0)

    def test_dataset_enrichment(self):
        csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "kanpur_nasa_power_daily.csv")
        df = pd.read_csv(csv_path)
        enriched = enrich_thermal_dataset(df)

        new_cols = ["Heat_Index_C", "Heat_Risk_Category", "PBLH_m", "Ventilation_Coeff_m2s", "NISI", "Inversion_Category"]
        for c in new_cols:
            self.assertIn(c, enriched.columns, f"Enrichment missed column: {c}")

        self.assertTrue((enriched["NISI"] >= 0).all())
        self.assertTrue((enriched["PBLH_m"] >= 150.0).all())


if __name__ == "__main__":
    unittest.main()
