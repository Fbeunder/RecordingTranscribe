#!/usr/bin/env python3
"""
Tests voor de recorder module van de Record en Transcribe applicatie.
"""

import unittest
from unittest.mock import patch, MagicMock
from modules.recorder import list_audio_devices, start_recording, stop_recording, save_recording


class TestRecorder(unittest.TestCase):
    """Test class voor de recorder module."""
    
    def test_list_audio_devices(self):
        """Test het oplijsten van audio devices."""
        # TODO: Implementeer deze test
        devices = list_audio_devices()
        self.assertIsInstance(devices, list)
    
    def test_start_recording(self):
        """Test het starten van een opname."""
        # TODO: Implementeer deze test
        result = start_recording(0)
        self.assertTrue(result)
    
    def test_stop_recording(self):
        """Test het stoppen van een opname."""
        # TODO: Implementeer deze test
        # Eerst een opname starten
        start_recording(0)
        # Dan stoppen
        audio_data = stop_recording()
        self.assertIsInstance(audio_data, bytes)
    
    def test_save_recording(self):
        """Test het opslaan van een opname."""
        # TODO: Implementeer deze test
        audio_data = b"test audio data"
        filename = "test_recording.wav"
        file_path = save_recording(audio_data, filename)
        self.assertIsInstance(file_path, str)


if __name__ == '__main__':
    unittest.main()
