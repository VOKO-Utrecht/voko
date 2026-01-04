# -*- coding: utf-8 -*-
import json
from django.test import TestCase
from django.http import HttpResponse

from api.utils import CSVResponse, JSONResponse


class JSONResponseTest(TestCase):
    """Tests for the JSONResponse class."""

    def test_returns_json_content_type(self):
        """Test response has JSON content type."""
        response = JSONResponse([{"key": "value"}])

        self.assertEqual(response["Content-Type"], "application/json")

    def test_returns_json_data(self):
        """Test response contains JSON data."""
        data = [{"name": "Test", "count": 42}]
        response = JSONResponse(data)

        result = json.loads(response.content)
        self.assertEqual(result, data)

    def test_handles_empty_list(self):
        """Test handles empty list."""
        response = JSONResponse([])

        result = json.loads(response.content)
        self.assertEqual(result, [])

    def test_handles_nested_data(self):
        """Test handles nested data structures."""
        data = [{"nested": {"key": "value"}, "list": [1, 2, 3]}]
        response = JSONResponse(data)

        result = json.loads(response.content)
        self.assertEqual(result[0]["nested"]["key"], "value")
        self.assertEqual(result[0]["list"], [1, 2, 3])


class CSVResponseTest(TestCase):
    """Tests for the CSVResponse class."""

    def test_returns_csv_content_type(self):
        """Test response has CSV content type."""
        response = CSVResponse([{"key": "value"}])

        self.assertEqual(response["Content-Type"], "text/csv")

    def test_csv_has_headers(self):
        """Test CSV contains column headers."""
        data = [{"name": "Test", "count": 42}]
        response = CSVResponse(data)

        content = response.content.decode("utf-8")
        # Headers should be in first line
        first_line = content.split("\n")[0]
        self.assertIn("name", first_line)
        self.assertIn("count", first_line)

    def test_csv_has_data_rows(self):
        """Test CSV contains data rows."""
        data = [{"name": "Test", "count": 42}]
        response = CSVResponse(data)

        content = response.content.decode("utf-8")
        self.assertIn("Test", content)
        self.assertIn("42", content)

    def test_handles_multiple_rows(self):
        """Test handles multiple rows."""
        data = [
            {"name": "First", "value": 1},
            {"name": "Second", "value": 2},
            {"name": "Third", "value": 3},
        ]
        response = CSVResponse(data)

        content = response.content.decode("utf-8")
        self.assertIn("First", content)
        self.assertIn("Second", content)
        self.assertIn("Third", content)
