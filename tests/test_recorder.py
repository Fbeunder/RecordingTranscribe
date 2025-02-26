#!/usr/bin/env python3
"""
Tests voor de recorder module van de Record en Transcribe applicatie.
"""

import unittest
import os
import time
from unittest.mock import patch, MagicMock
import pyaudio
import io
import wave
from modules.recorder import list_audio_devices, start_recording, stop_recording, save_recording


class TestRecorder(unittest.TestCase):
    """Test class voor de recorder module."""
    
    @patch('pyaudio.PyAudio')
    def test_list_audio_devices(self, mock_pyaudio):
        """Test het oplijsten van audio devices."""
        # Mock setup
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        # Mock 2 apparaten: 1 input en 1 output apparaat
        mock_pyaudio_instance.get_device_count.return_value = 2
        
        def get_device_info_side_effect(index):
            if index == 0:
                return {
                    'index': 0,
                    'name': 'Test Microphone',
                    'maxInputChannels': 2,
                    'maxOutputChannels': 0
                }
            else:
                return {
                    'index': 1,
                    'name': 'Test Speaker',
                    'maxInputChannels': 0,
                    'maxOutputChannels': 2
                }
        
        mock_pyaudio_instance.get_device_info_by_index.side_effect = get_device_info_side_effect
        
        # Test uitvoeren
        devices = list_audio_devices()
        
        # Verificatie
        self.assertEqual(len(devices), 1)  # Alleen het input apparaat moet geretourneerd worden
        self.assertEqual(devices[0]['id'], 0)
        self.assertEqual(devices[0]['name'], 'Test Microphone')
        self.assertEqual(devices[0]['channels'], 2)
    
    @patch('pyaudio.PyAudio')
    @patch('threading.Thread')
    def test_start_recording(self, mock_thread, mock_pyaudio):
        """Test het starten van een opname."""
        # Mock setup
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        mock_stream = MagicMock()
        mock_pyaudio_instance.open.return_value = mock_stream
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Test uitvoeren
        result = start_recording(0)
        
        # Verificatie
        self.assertTrue(result)
        mock_pyaudio_instance.open.assert_called_once()
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    @patch('pyaudio.PyAudio')
    @patch('threading.Thread')
    @patch('io.BytesIO')
    @patch('wave.open')
    def test_stop_recording(self, mock_wave_open, mock_bytesio, mock_thread, mock_pyaudio):
        """Test het stoppen van een opname."""
        # Mock setup
        mock_pyaudio_instance = MagicMock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        mock_stream = MagicMock()
        mock_pyaudio_instance.open.return_value = mock_stream
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        mock_bytesio_instance = MagicMock()
        mock_bytesio.return_value = mock_bytesio_instance
        mock_bytesio_instance.getvalue.return_value = b'test audio data'
        
        mock_wave_file = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        
        # Start opname
        start_recording(0)
        
        # Test uitvoeren
        audio_data = stop_recording()
        
        # Verificatie
        self.assertEqual(audio_data, b'test audio data')
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_pyaudio_instance.terminate.assert_called_once()
        mock_wave_file.writeframes.assert_called_once()
    
    @patch('modules.file_handler.save_file')
    def test_save_recording(self, mock_save_file):
        """Test het opslaan van een opname."""
        # Mock setup
        mock_save_file.return_value = '/path/to/test_recording.wav'
        
        # Test uitvoeren
        audio_data = b"test audio data"
        filename = "test_recording.wav"
        file_path = save_recording(audio_data, filename)
        
        # Verificatie
        self.assertEqual(file_path, '/path/to/test_recording.wav')
        mock_save_file.assert_called_once_with(audio_data, filename)
        
    def test_save_recording_adds_wav_extension(self):
        """Test dat .wav extensie wordt toegevoegd als deze ontbreekt."""
        with patch('modules.file_handler.save_file') as mock_save_file:
            mock_save_file.return_value = '/path/to/test_recording.wav'
            
            # Test uitvoeren
            audio_data = b"test audio data"
            filename = "test_recording"  # Geen extensie
            save_recording(audio_data, filename)
            
            # Verificatie
            mock_save_file.assert_called_once_with(audio_data, "test_recording.wav")


if __name__ == '__main__':
    unittest.main()
