#!/usr/bin/env python3
"""
Integratie tests voor de Record en Transcribe applicatie.

Deze tests controleren of de verschillende modules goed samenwerken
en of de complete workflow (opnemen → opslaan → transcriberen → opslaan)
correct functioneert. Ook worden foutscenario's getest om te zorgen dat
de applicatie robuust is en fouten goed afhandelt.
"""

import unittest
import os
import tempfile
import wave
import json
import shutil
from unittest.mock import patch, MagicMock, mock_open
from modules.recorder import list_audio_devices, start_recording, stop_recording, save_recording
from modules.transcriber import transcribe_audio, save_transcription, supported_languages
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
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
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
        mock_transcribe.assert_called_once_with(audio_file, 'nl-NL')  # Check default language
    
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
    
    @patch('modules.file_handler.get_download_folder')
    @patch('modules.recorder.list_audio_devices')
    def test_no_devices_available(self, mock_list_devices, mock_get_download_folder):
        """Test het gedrag wanneer er geen audio apparaten beschikbaar zijn."""
        # Setup mocks
        mock_list_devices.return_value = []  # Geen apparaten beschikbaar
        mock_get_download_folder.return_value = self.test_dir
        
        # Test de API endpoint
        response = self.client.get('/api/devices')
        data = json.loads(response.data)
        
        # Er zou nog steeds een default device moeten zijn
        self.assertEqual(response.status_code, 200)
        self.assertIn('devices', data)
        self.assertEqual(len(data['devices']), 1)
        self.assertEqual(data['devices'][0]['name'], 'Default Microphone')
    
    @patch('modules.recorder.start_recording')
    def test_start_recording_fail(self, mock_start_recording):
        """Test foutafhandeling wanneer het starten van een opname mislukt."""
        # Setup mocks voor mislukte opname
        mock_start_recording.return_value = False
        
        # Test API endpoint
        response = self.client.post('/api/record/start', 
                                   json={'device_id': 0},
                                   content_type='application/json')
        data = json.loads(response.data)
        
        # Controleer of de juiste foutmelding wordt gegeven
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', data)
        self.assertIn('details', data)
    
    @patch('modules.recorder.stop_recording')
    def test_stop_recording_no_audio(self, mock_stop_recording):
        """Test foutafhandeling wanneer er geen audio is opgenomen."""
        # Setup mocks voor lege audio
        mock_stop_recording.return_value = b''
        
        # Test API endpoint
        response = self.client.post('/api/record/stop',
                                   content_type='application/json')
        data = json.loads(response.data)
        
        # Controleer of de juiste foutmelding wordt gegeven
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Geen audio data ontvangen')
    
    @patch('os.path.exists')
    def test_transcribe_nonexistent_file(self, mock_exists):
        """Test foutafhandeling bij transcriptie van niet-bestaand bestand."""
        # Setup mocks voor niet-bestaand bestand
        mock_exists.return_value = False
        
        # Test API endpoint
        response = self.client.post('/api/transcribe',
                                   json={'audio_file': '/niet_bestaand_bestand.wav'},
                                   content_type='application/json')
        data = json.loads(response.data)
        
        # Controleer of de juiste foutmelding wordt gegeven
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Audiobestand niet gevonden')
    
    def test_transcribe_no_file_specified(self):
        """Test foutafhandeling wanneer geen bestand is opgegeven voor transcriptie."""
        # Test API endpoint zonder bestand
        response = self.client.post('/api/transcribe',
                                   json={},  # Lege JSON data
                                   content_type='application/json')
        data = json.loads(response.data)
        
        # Controleer of de juiste foutmelding wordt gegeven
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Geen audiobestand opgegeven')
    
    def test_invalid_json_data(self):
        """Test foutafhandeling bij ongeldige JSON data."""
        # Test API endpoint met ongeldige JSON
        response = self.client.post('/api/record/start',
                                   data='Dit is geen geldige JSON',
                                   content_type='application/json')
        
        # Controleer of de juiste foutmelding wordt gegeven
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('modules.transcriber.transcribe_audio')
    @patch('modules.file_handler.save_file')
    @patch('os.path.exists')
    def test_transcribe_with_unsupported_language(self, mock_exists, mock_save_file, mock_transcribe):
        """Test foutafhandeling bij transcriptie met niet-ondersteunde taal."""
        # Setup mocks
        mock_exists.return_value = True
        mock_save_file.return_value = os.path.join(self.test_dir, "test_recording.txt")
        
        # Test API endpoint met ongeldige taal
        response = self.client.post('/api/transcribe',
                                   json={
                                       'audio_file': os.path.join(self.test_dir, "test_recording.wav"),
                                       'language': 'xx-XX'  # Niet-bestaande taalcode
                                   },
                                   content_type='application/json')
        data = json.loads(response.data)
        
        # Controleer of de juiste foutmelding wordt gegeven
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Niet-ondersteunde taal')
    
    @patch('modules.transcriber.transcribe_audio')
    @patch('os.path.exists')
    def test_transcribe_no_speech_detected(self, mock_exists, mock_transcribe):
        """Test het gedrag wanneer geen spraak wordt herkend in een opname."""
        # Setup mocks
        mock_exists.return_value = True
        mock_transcribe.return_value = "Kon geen spraak herkennen in de opname."
        
        # Test API endpoint
        response = self.client.post('/api/transcribe',
                                   json={'audio_file': os.path.join(self.test_dir, "test_recording.wav")},
                                   content_type='application/json')
        data = json.loads(response.data)
        
        # Controleer of de juiste waarschuwing wordt gegeven
        self.assertEqual(response.status_code, 200)
        self.assertIn('warning', data)
        self.assertEqual(data['warning'], 'Geen spraak herkend')
    
    def test_api_languages(self):
        """Test het ophalen van ondersteunde talen."""
        # Test API endpoint
        response = self.client.get('/api/languages')
        data = json.loads(response.data)
        
        # Controleer of de talen correct worden teruggegeven
        self.assertEqual(response.status_code, 200)
        self.assertIn('languages', data)
        self.assertIn('nl-NL', data['languages'])
        self.assertEqual(data['languages']['nl-NL'], 'Nederlands')
    
    def test_not_found_error(self):
        """Test 404 afhandeling voor niet-bestaande endpoints."""
        # Test niet-bestaande endpoint
        response = self.client.get('/api/niet_bestaand_endpoint')
        
        # Controleer of 404 correct wordt afgehandeld
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
