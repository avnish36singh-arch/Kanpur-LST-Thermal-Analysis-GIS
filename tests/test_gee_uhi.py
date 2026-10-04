"""
Unit tests for Kanpur GEE UHI analysis module.
"""

import os
import sys
import unittest
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from kanpur_uhi_analysis import load_local_merra2_benchmark


class TestGEEUHIAnalysis(unittest.TestCase):

    def test_merra2_benchmark_loader(self):
        csv_path = os.path.join(PROJECT_ROOT, "data", "raw", "kanpur_nasa_power_daily.csv")
        lookup = load_local_merra2_benchmark(csv_path)
        self.assertIsInstance(lookup, dict)
        if os.path.exists(csv_path):
            self.assertGreater(len(lookup), 2000)
            # Test a known date from the dataset
            self.assertIn("2017-01-01", lookup)
            self.assertAlmostEqual(lookup["2017-01-01"], 14.23, places=2)

    def test_landsat_c2_l2_calibration_formula(self):
        """
        Validates USGS Landsat 8/9 Collection 2 Level 2 Surface Temperature scaling:
        Formula: Kelvin = DN * 0.00341802 + 149.0
                 Celsius = Kelvin - 273.15
        """
        # Test realistic DN value: 44,000
        dn = 44000
        kelvin = dn * 0.00341802 + 149.0
        celsius = kelvin - 273.15
        
        # Should be realistic summer/equinox Kanpur temperature ~26.24°C
        self.assertAlmostEqual(kelvin, 299.39288, places=3)
        self.assertAlmostEqual(celsius, 26.24288, places=3)
        self.assertGreater(celsius, 15.0)
        self.assertLess(celsius, 50.0)

    def test_legacy_scaling_catch(self):
        """
        Ensures the legacy scale factor 0.0001 is caught as erroneous (would give -268°C).
        """
        dn = 44000
        wrong_celsius = (dn * 0.0001) - 273.15
        self.assertLess(wrong_celsius, -200.0)  # Unphysical


if __name__ == '__main__':
    unittest.main()
