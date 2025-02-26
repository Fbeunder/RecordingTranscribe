#!/usr/bin/env python3
"""
Tests voor de file_handler module van de Record en Transcribe applicatie.
"""

import unittest
import os
from unittest.mock import patch, mock_open
from modules.file_handler import get_download_folder, save_file, load_file


class TestFileHandler(unittest.TestCase):
    """Test class voor de file_handler module."""
    
    def test_get_download_folder(self):
        """Test het bepalen van de download folder."""
        # TODO: Implementeer deze test
        folder = get_download_folder()
        self.assertIsInstance(folder, str)
        self.assertTrue(os.path.exists(folder))
    
    def test_save_file(self):
        """Test het opslaan van een bestand."""
        # TODO: Implementeer deze test
        with patch('builtins.open', mock_open()) as mock_file:
            data = "test data"
            filename = "test.txt"
            file_path = save_file(data, filename)
            self.assertIsInstance(file_path, str)
    
    def test_load_file(self):
        """Test het laden van een bestand."""
        # TODO: Implementeer deze test
        with patch('builtins.open', mock_open(read_data="test data")):
            file_content = load_file("test.txt")
            self.assertIsInstance(file_content, (bytes, str))


if __name__ == '__main__':
    unittest.main()
