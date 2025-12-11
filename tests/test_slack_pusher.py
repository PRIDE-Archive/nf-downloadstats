"""
Unit tests for SlackPusher class.
"""
import unittest
import tempfile
import os
from unittest.mock import patch, Mock
from filedownloadstat.slack_pusher import SlackPusher, push_to_slack
from filedownloadstat.exceptions import ValidationError, SlackPushError


class TestSlackPusher(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_webhook_url = "https://hooks.slack.com/services/test/webhook/url"
        self.test_file = os.path.join(self.temp_dir, "test_report.html")
        with open(self.test_file, 'w') as f:
            f.write("<html><body>Test Report</body></html>")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_valid_webhook(self):
        """Test SlackPusher initialization with valid webhook URL."""
        pusher = SlackPusher(self.test_webhook_url)
        self.assertEqual(pusher.webhook_url, self.test_webhook_url)

    def test_init_with_empty_webhook_raises_error(self):
        """Test SlackPusher initialization with empty webhook raises ValidationError."""
        with self.assertRaises(ValidationError):
            SlackPusher("")

    @patch('filedownloadstat.slack_pusher.requests.post')
    def test_push_report_success(self, mock_post):
        """Test push_report with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        pusher = SlackPusher(self.test_webhook_url)
        result = pusher.push_report(self.test_file, "Test Title")
        
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('filedownloadstat.slack_pusher.requests.post')
    def test_push_report_failure(self, mock_post):
        """Test push_report with failed response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        pusher = SlackPusher(self.test_webhook_url)
        result = pusher.push_report(self.test_file, "Test Title")
        
        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch('filedownloadstat.slack_pusher.requests.post')
    def test_push_report_file_not_found(self, mock_post):
        """Test push_report with nonexistent file."""
        pusher = SlackPusher(self.test_webhook_url)
        result = pusher.push_report("/nonexistent/file.html", "Test Title")
        
        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('filedownloadstat.slack_pusher.requests.post')
    def test_push_report_network_error(self, mock_post):
        """Test push_report with network error."""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")
        
        pusher = SlackPusher(self.test_webhook_url)
        result = pusher.push_report(self.test_file, "Test Title")
        
        self.assertFalse(result)

    @patch('filedownloadstat.slack_pusher.requests.post')
    def test_push_report_with_tsv_file(self, mock_post):
        """Test push_report with TSV file."""
        tsv_file = os.path.join(self.temp_dir, "test.tsv")
        with open(tsv_file, 'w') as f:
            f.write("col1\tcol2\nval1\tval2\n")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        pusher = SlackPusher(self.test_webhook_url)
        result = pusher.push_report(tsv_file, "Test Title")
        
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('filedownloadstat.slack_pusher.requests.post')
    def test_push_to_slack_convenience_function(self, mock_post):
        """Test push_to_slack convenience function."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = push_to_slack(self.test_file, self.test_webhook_url, "Test Title")
        
        self.assertTrue(result)
        mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()

