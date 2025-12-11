"""
Extended unit tests for LogFileParser class.
Tests for new fields and error handling.
"""
import unittest
import os
import yaml
from datetime import datetime
from filedownloadstat.log_file_parser import LogFileParser


class TestLogParserExtended(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load YAML configuration before running tests."""
        yaml_path = os.path.join(os.path.dirname(__file__), "../params/pride-local-params.yml")
        try:
            with open(yaml_path, "r") as file:
                cls.config = yaml.safe_load(file)
        except FileNotFoundError:
            # Use default config if file doesn't exist
            cls.config = {
                "resource_identifiers": ["/pride/data/archive"],
                "completeness": ["complete", "incomplete"]
            }

        cls.parser = LogFileParser(
            "",
            resource_list=cls.config.get("resource_identifiers", ["/pride/data/archive"]),
            completeness_list=cls.config.get("completeness", ["complete"]),
            accession_pattern_list=["^PXD\\d{6}$"]
        )

    def test_parse_row_with_new_fields(self):
        """Test parsing a row includes new fields: timestamp, geoip_region_name, geoip_city_name, geo_location."""
        row = [
            "2023-01-01T23:57:16.000Z",
            "caf4815df53c650523eb4943a05bc7b7906e5507",
            "669943668",
            "/pride/data/archive/2016/12/PXD004242/filename.raw",
            "OUT",
            "03dbae9a96db63fa62487cd3c134d05230858127",
            "Complete",
            "United Kingdom",
            "Cambridgeshire",
            "Sawston",
            "52.1202,0.1845",
            "http",
            "public"
        ]
        parsed = self.parser.parse_row(row, 1)

        self.assertIsNotNone(parsed)
        self.assertIn("timestamp", parsed)
        self.assertIn("geoip_region_name", parsed)
        self.assertIn("geoip_city_name", parsed)
        self.assertIn("geo_location", parsed)
        
        self.assertEqual(parsed["timestamp"], "2023-01-01T23:57:16.000Z")
        self.assertEqual(parsed["geoip_region_name"], "Cambridgeshire")
        self.assertEqual(parsed["geoip_city_name"], "Sawston")
        self.assertEqual(parsed["geo_location"], "52.1202,0.1845")

    def test_clean_geoip_value_with_placeholder(self):
        """Test clean_geoip_value filters placeholder values."""
        # Test with placeholder pattern {geoip_region_name}
        result = self.parser.clean_geoip_value("{geoip_region_name}")
        self.assertEqual(result, "")
        
        # Test with placeholder pattern %{geoip_city_name}
        result = self.parser.clean_geoip_value("%{geoip_city_name}")
        self.assertEqual(result, "")
        
        # Test with real value
        result = self.parser.clean_geoip_value("Cambridgeshire")
        self.assertEqual(result, "Cambridgeshire")
        
        # Test with empty string
        result = self.parser.clean_geoip_value("")
        self.assertEqual(result, "")
        
        # Test with None
        result = self.parser.clean_geoip_value(None)
        self.assertEqual(result, "")

    def test_parse_row_with_empty_geoip_fields(self):
        """Test parsing row with empty geoip fields."""
        row = [
            "2023-01-01T23:57:16.000Z",
            "caf4815df53c650523eb4943a05bc7b7906e5507",
            "669943668",
            "/pride/data/archive/2016/12/PXD004242/filename.raw",
            "OUT",
            "03dbae9a96db63fa62487cd3c134d05230858127",
            "Complete",
            "United Kingdom",
            "",  # Empty geoip_region_name
            "",  # Empty geoip_city_name
            "",  # Empty geo_location
            "http",
            "public"
        ]
        parsed = self.parser.parse_row(row, 1)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["geoip_region_name"], "")
        self.assertEqual(parsed["geoip_city_name"], "")
        self.assertEqual(parsed["geo_location"], "")

    def test_parse_row_with_placeholder_geoip_values(self):
        """Test parsing row with placeholder geoip values."""
        row = [
            "2023-01-01T23:57:16.000Z",
            "caf4815df53c650523eb4943a05bc7b7906e5507",
            "669943668",
            "/pride/data/archive/2016/12/PXD004242/filename.raw",
            "OUT",
            "03dbae9a96db63fa62487cd3c134d05230858127",
            "Complete",
            "United Kingdom",
            "{geoip_region_name}",  # Placeholder
            "%{geoip_city_name}",    # Placeholder
            "52.1202,0.1845",
            "http",
            "public"
        ]
        parsed = self.parser.parse_row(row, 1)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["geoip_region_name"], "")
        self.assertEqual(parsed["geoip_city_name"], "")

    def test_clean_timestamp(self):
        """Test clean_timestamp method."""
        # Test with microseconds
        result = self.parser.clean_timestamp("2023-01-01T23:57:16.000Z")
        self.assertEqual(result, "2023-01-01T23:57:16.000")
        
        # Test with long microseconds
        result = self.parser.clean_timestamp("2023-01-01T23:57:16.419698061Z")
        self.assertEqual(result, "2023-01-01T23:57:16.419698")
        
        # Test without microseconds
        result = self.parser.clean_timestamp("2023-01-01T23:57:16Z")
        self.assertEqual(result, "2023-01-01T23:57:16")

    def test_parse_row_incomplete_status(self):
        """Test parsing row with incomplete status."""
        row = [
            "2023-01-01T23:57:16.000Z",
            "caf4815df53c650523eb4943a05bc7b7906e5507",
            "669943668",
            "/pride/data/archive/2016/12/PXD004242/filename.raw",
            "OUT",
            "03dbae9a96db63fa62487cd3c134d05230858127",
            "Partial",  # Incomplete status
            "United Kingdom",
            "Cambridgeshire",
            "Sawston",
            "52.1202,0.1845",
            "http",
            "public"
        ]
        
        # Update parser to accept incomplete
        parser = LogFileParser(
            "",
            resource_list=["/pride/data/archive"],
            completeness_list=["complete", "incomplete"],
            accession_pattern_list=["^PXD\\d{6}$"]
        )
        
        parsed = parser.parse_row(row, 1)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["completed"], "partial")


if __name__ == '__main__':
    unittest.main()

