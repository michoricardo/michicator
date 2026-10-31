import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api import webhook


class FugglerGalleryTests(unittest.TestCase):
    @patch("api.webhook._send_photo")
    @patch("api.webhook._send")
    def test_fuggler_gallery_sends_photo_when_file_id_exists(self, mock_send, mock_send_photo):
        memory = Mock()
        memory.get_fugglers.return_value = [{
            "nombre": "Monito rosa",
            "descripcion": "cara redonda",
            "file_id": "abc123",
            "foto_url": "",
        }]

        webhook._cmd_fugglers("123", memory)

        mock_send_photo.assert_called_once_with(
            "123",
            file_id="abc123",
            caption="<b>Monito rosa</b>\ncara redonda",
        )
        mock_send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
