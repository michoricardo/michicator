import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api import webhook


class SendFallbackTests(unittest.TestCase):
    @patch("requests.post")
    def test_send_retries_without_parse_mode_on_html_entity_error(self, mock_post):
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

        first = unittest.mock.Mock()
        first.ok = False
        first.status_code = 400
        first.text = '{"ok":false,"error_code":400,"description":"Bad Request: can\'t parse entities: Unsupported start tag \\\"item\\\""}'

        second = unittest.mock.Mock()
        second.ok = True
        second.status_code = 200
        second.text = "{}"

        mock_post.side_effect = [first, second]

        webhook._send("123", "<b>hello</b> <item>")
        self.assertEqual(mock_post.call_count, 2)
        self.assertNotIn("parse_mode", mock_post.call_args_list[1].kwargs["json"])


if __name__ == "__main__":
    unittest.main()
