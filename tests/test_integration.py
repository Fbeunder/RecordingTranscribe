#!/usr/bin/env python3
"""
Integratie tests voor de Record en Transcribe applicatie.

Deze tests controleren of de verschillende modules goed samenwerken
en of de complete workflow (opnemen → opslaan → transcriberen → opslaan)
correct functioneert.
"""

import unittest
import os
import tempfile
import wave
import json
from unittest.mock import patch, MagicMock, mock_open
from modules.recorder import list_audio_devices, start_recording, stop_recording, save_recording
from modules.transcriber import transcribe_audio, save_transcription
from modules.file_handler import save_file, load_file
from app import create_app


class TestIntegration(unittest.TestCase):
    """Integratie test class voor de volledige applicatie workflow."""
    
    def setUp(self):
        """Setup voor de tests."""
        # Maak een test Flask app aan
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Maak een tijdelijke directory voor testbestanden
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Teardown na de tests."""
        self.app_context.pop()
        
        # Verwijder tijdelijke bestanden
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)
    
    @patch('modules.file_handler.get_download_folder')
    @patch('modules.file_handler.save_file')
    @patch('modules.transcriber.transcribe_audio')
    @patch('modules.recorder.stop_recording')
    @patch('modules.recorder.start_recording')
    @patch('modules.recorder.list_audio_devices')
    def test_complete_workflow(self, mock_list_devices, mock_start_recording, 
                              mock_stop_recording, mock_transcribe, 
                              mock_save_file, mock_get_download_folder):
        """Test de complete workflow van apparaten oplijsten tot transcriptie opslaan."""
        # Setup mocks
        mock_list_devices.return_value = [{'id': 0, 'name': 'Test Microphone', 'channels': 1}]
        mock_start_recording.return_value = True
        mock_stop_recording.return_value = b'test audio data'
        mock_transcribe.return_value = "Dit is een test transcriptie."
        mock_save_file.side_effect = lambda data, filename, folder=None: os.path.join(self.test_dir, filename)
        mock_get_download_folder.return_value = self.test_dir
        
        # 1. Test het oplijsten van apparaten
        response = self.client.get('/api/devices')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('devices', data)
        self.assertEqual(len(data['devices']), 1)
        self.assertEqual(data['devices'][0]['id'], 0)
        
        # 2. Test het starten van een opname
        response = self.client.post('/api/record/start', 
                                   json={'device_id': 0},
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'recording')
        mock_start_recording.assert_called_once_with(0)
        
        # 3. Test het stoppen van een opname
        response = self.client.post('/api/record/stop',
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'stopped')
        self.assertIn('filename', data)
        self.assertIn('file_path', data)
        mock_stop_recording.assert_called_once()
        mock_save_file.assert_called_once()
        
        # 4. Test het transcriberen van de opname
        audio_file = data['file_path']
        response = self.client.post('/api/transcribe',
                                   json={'audio_file': audio_file},
                                   content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['text'], "Dit is een test transcriptie.")
        self.assertIn('filename', data)
        self.assertIn('file_path', data)
        mock_transcribe.assert_called_once_with(audio_file)
    
    @patch('os.path.exists')
    @patch('wave.open')
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_recorder_to_transcriber_integration(self, mock_audio_file, mock_recognizer, 
                                                mock_wave_open, mock_exists):
        """Test de integratie tussen recorder en transcriber modules."""
        # Maak een test WAV bestand met mock
        mock_exists.return_value = True
        
        # Mocks voor stop_recording (recorder.py)
        mock_wave_context = MagicMock()
        mock_wave_open.return_value.__enter__.return_value = mock_wave_context
        
        # Mocks voor transcribe_audio (transcriber.py)
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "Dit is een test transcriptie."
        
        mock_audio_file_instance = MagicMock()
        mock_audio_file_context = MagicMock()
        mock_audio_file.return_value = mock_audio_file_context
        mock_audio_file_context.__enter__.return_value = mock_audio_file_instance
        
        # Simuleer opname en opslaan
        with patch('modules.file_handler.save_file') as mock_save_file:
            mock_save_file.return_value = os.path.join(self.test_dir, "test_recording.wav")
            
            # Opnemen en stoppen
            start_recording(0)
            audio_data = stop_recording()
            file_path = save_recording(audio_data, "test_recording.wav")
            
            # Transcriberen
            transcription = transcribe_audio(file_path)
            text_path = save_transcription(transcription, "test_recording.txt")
            
            # Verificatie
            self.assertEqual(transcription, "Dit is een test transcriptie.")
            mock_save_file.assert_any_call(audio_data, "test_recording.wav")
            
    @patch('modules.file_handler.get_download_folder')
    def test_file_handler_integration(self, mock_get_download_folder):
        """Test de integratie van de file_handler module met andere modules."""
        # Setup mocks
        mock_get_download_folder.return_value = self.test_dir
        
        # Maak test bestanden
        test_audio_data = b'test audio data'
        test_text = "Dit is een test transcriptie."
        
        # Test save_file met bytes (audio)
        with patch('builtins.open', mock_open()) as mock_file:
            audio_path = save_file(test_audio_data, "test_audio.wav")
            mock_file.assert_called_once()
            # Controleer dat open aangeroepen wordt met 'wb' voor binaire data
            self.assertEqual(mock_file.call_args[0][1], 'wb')
        
        # Test save_file met tekst (transcriptie)
        with patch('builtins.open', mock_open()) as mock_file:
            text_path = save_file(test_text, "test_transcription.txt")
            mock_file.assert_called_once()
            # Controleer dat open aangeroepen wordt met 'w' voor tekstdata
            self.assertEqual(mock_file.call_args[0][1], 'w')
        
        # Test load_file
        with patch('builtins.open', mock_open(read_data=test_text)) as mock_file:
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                loaded_text = load_file(text_path)
                self.assertEqual(loaded_text, test_text)


if __name__ == '__main__':
    unittest.main()
