import unittest
from unittest.mock import patch, MagicMock
import json

# Assuming all functions are part of a module named 'aws_analysis'
from analyzer import update_cache_for_check_ids, load_cache, save_cache


class TestCacheRefresh(unittest.TestCase):
    def setUp(self):
        # Setup a mock cache for testing
        self.mock_cache = {
            "Check Title 1": {
                "check_id": "1",
                "Pillar": "Reliability",
                "Question": "How do you manage failures?",
                "Severity": "High",
                "Check Title": "Ensure high availability",
                "Check Description": "Your system must be available across multiple regions.",
                "Resource Type": "EC2",
                "suggestion": "Use autoscaling.",
            },
            "Check Title 2": {
                "check_id": "2",
                "Pillar": "Security",
                "Question": "How do you secure your data?",
                "Severity": "Medium",
                "Check Title": "Encrypt data at rest",
                "Check Description": "All data must be encrypted when stored.",
                "Resource Type": "S3",
                "suggestion": "Use AWS KMS.",
            },
        }

    @patch("analyzer.analyze_finding_with_ollama")
    def test_update_cache_for_check_ids(self, mock_analyze_finding_with_ollama):
        # Setup mock behavior
        mock_analyze_finding_with_ollama.return_value = "New suggestion after refresh."

        # IDs to refresh
        update_check_ids = ["1"]  # Use string to match the check_id type in the cache

        # Call the function to update cache
        updated_cache = update_cache_for_check_ids(update_check_ids, self.mock_cache)

        # Assertions to verify the behavior
        self.assertIn("Check Title 1", updated_cache)
        self.assertEqual(
            updated_cache["Check Title 1"]["suggestion"],
            "New suggestion after refresh.",
        )
        self.assertEqual(updated_cache["Check Title 2"]["suggestion"], "Use AWS KMS.")

        # Verify that the function to generate suggestions was called only for Check ID 1
        mock_analyze_finding_with_ollama.assert_called_once_with(
            self.mock_cache["Check Title 1"], "1", refresh=True, additional_info=None
        )


if __name__ == "__main__":
    unittest.main()
