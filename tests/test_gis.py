"""
Unit tests for QGIS vector layers and spatial geometry schema compliance.
Compatible with standard library unittest and pytest.
"""

import os
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QGIS_DIR = os.path.join(PROJECT_ROOT, "outputs", "qgis")


class TestGISVectorLayers(unittest.TestCase):

    def test_qgis_layers_exist(self):
        expected_files = [
            "kanpur_thermal_zones.geojson",
            "kanpur_cpcb_stations.geojson",
            "kanpur_ganga_riparian.geojson",
            "kanpur_microclimate_transect.geojson",
            "kanpur_thermal_zones.qml"
        ]
        for fname in expected_files:
            fpath = os.path.join(QGIS_DIR, fname)
            self.assertTrue(os.path.exists(fpath), f"Missing GIS layer: {fname}")

    def test_thermal_zones_geojson_schema(self):
        fpath = os.path.join(QGIS_DIR, "kanpur_thermal_zones.geojson")
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("type"), "FeatureCollection")
        features = data.get("features", [])
        self.assertEqual(len(features), 5, f"Expected 5 microclimate zones, found {len(features)}")

        for feat in features:
            self.assertEqual(feat.get("type"), "Feature")
            geom = feat.get("geometry", {})
            self.assertEqual(geom.get("type"), "Polygon")

            coords = geom.get("coordinates", [])[0]
            self.assertEqual(coords[0], coords[-1], "Polygon geometry is not closed")

            # Check bounds: Kanpur metropolitan domain
            for lon, lat in coords:
                self.assertTrue(80.10 <= lon <= 80.55, f"Longitude {lon} out of Kanpur bounds")
                self.assertTrue(26.35 <= lat <= 26.60, f"Latitude {lat} out of Kanpur bounds")

            props = feat.get("properties", {})
            self.assertIn("zone_id", props)
            self.assertIn("mean_uhi_offset_c", props)
            self.assertIn("area_sqkm", props)

    def test_cpcb_stations_geojson(self):
        fpath = os.path.join(QGIS_DIR, "kanpur_cpcb_stations.geojson")
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("type"), "FeatureCollection")
        features = data.get("features", [])
        self.assertEqual(len(features), 2, "Expected 2 CAAQMS stations")

        station_names = [feat["properties"]["name"] for feat in features]
        self.assertIn("NSI Kalyanpur", station_names)
        self.assertIn("Nehru Nagar", station_names)

    def test_qgis_qml_style(self):
        qml_path = os.path.join(QGIS_DIR, "kanpur_thermal_zones.qml")
        with open(qml_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<qgis", content)
        self.assertIn("Central Urban Core", content)
        self.assertIn("Ganga Riparian", content)


if __name__ == "__main__":
    unittest.main()
