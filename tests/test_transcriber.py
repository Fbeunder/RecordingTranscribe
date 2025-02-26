#!/usr/bin/env python3
"""
Tests voor de transcriber module van de Record en Transcribe applicatie.
"""

import unittest
import os
from unittest.mock import patch, MagicMock, mock_open
import speech_recognition as sr
from modules.transcriber import transcribe_audio, save_transcription, transcribe_with_options, supported_languages


class TestTranscriber(unittest.TestCase):
    """Test class voor de transcriber module."""
    
    @patch('os.path.exists')
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_transcribe_audio_success(self, mock_audio_file, mock_recognizer, mock_exists):
        """Test een succesvolle transcriptie."""
        # Setup mocks
        mock_exists.return_value = True
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "Dit is een test transcriptie."
        
        mock_audio_file_instance = MagicMock()
        mock_audio_file_context = MagicMock()
        mock_audio_file.return_value = mock_audio_file_context
        mock_audio_file_context.__enter__.return_value = mock_audio_file_instance
        
        # Roep de functie aan
        result = transcribe_audio("test_audio.wav", language="nl-NL")
        
        # Controleer resultaten
        self.assertEqual(result, "Dit is een test transcriptie.")
        mock_recognizer_instance.recognize_google.assert_called_once()
        mock_recognizer_instance.recognize_google.assert_called_with(
            mock_recognizer_instance.record.return_value, 
            language="nl-NL"
        )
    
    @patch('os.path.exists')
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test transcriptie met een niet-bestaand bestand."""
        # Setup mock
        mock_exists.return_value = False
        
        # Verwacht FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            transcribe_audio("niet_bestaand_bestand.wav")
    
    @patch('os.path.exists')
    def test_transcribe_audio_invalid_format(self, mock_exists):
        """Test transcriptie met een ongeldig bestandsformaat."""
        # Setup mock
        mock_exists.return_value = True
        
        # Verwacht ValueError
        with self.assertRaises(ValueError):
            transcribe_audio("test_audio.mp3")  # Geen WAV-bestand
    
    @patch('os.path.exists')
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_transcribe_audio_unknown_value_error(self, mock_audio_file, mock_recognizer, mock_exists):
        """Test transcriptie waarbij geen spraak herkend wordt."""
        # Setup mocks
        mock_exists.return_value = True
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.side_effect = sr.UnknownValueError()
        
        mock_audio_file_instance = MagicMock()
        mock_audio_file_context = MagicMock()
        mock_audio_file.return_value = mock_audio_file_context
        mock_audio_file_context.__enter__.return_value = mock_audio_file_instance
        
        # Roep de functie aan
        result = transcribe_audio("test_audio.wav")
        
        # Controleer resultaten
        self.assertEqual(result, "Kon geen spraak herkennen in de opname.")
    
    @patch('os.path.exists')
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_transcribe_audio_request_error(self, mock_audio_file, mock_recognizer, mock_exists):
        """Test transcriptie waarbij een RequestError optreedt."""
        # Setup mocks
        mock_exists.return_value = True
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.side_effect = sr.RequestError("API niet beschikbaar")
        
        mock_audio_file_instance = MagicMock()
        mock_audio_file_context = MagicMock()
        mock_audio_file.return_value = mock_audio_file_context
        mock_audio_file_context.__enter__.return_value = mock_audio_file_instance
        
        # Verwacht Exception
        with self.assertRaises(Exception) as context:
            transcribe_audio("test_audio.wav")
        
        self.assertIn("Kon de spraakherkenningsdienst niet bereiken", str(context.exception))
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_transcribe_with_options_google(self, mock_audio_file, mock_recognizer):
        """Test transcriptie met aangepaste opties - Google engine."""
        # Setup mocks
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "Dit is een test transcriptie."
        
        mock_audio_file_instance = MagicMock()
        mock_audio_file_context = MagicMock()
        mock_audio_file.return_value = mock_audio_file_context
        mock_audio_file_context.__enter__.return_value = mock_audio_file_instance
        
        # Roep de functie aan
        options = {'language': 'nl-NL', 'engine': 'google'}
        result = transcribe_with_options("test_audio.wav", options)
        
        # Controleer resultaten
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "Dit is een test transcriptie.")
        self.assertEqual(result['engine_used'], 'google')
        self.assertEqual(result['language'], 'nl-NL')
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_transcribe_with_options_sphinx_english(self, mock_audio_file, mock_recognizer):
        """Test transcriptie met aangepaste opties - Sphinx engine in het Engels."""
        # Setup mocks
        mock_recognizer_instance = MagicMock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_sphinx.return_value = "This is a test transcription."
        
        mock_audio_file_instance = MagicMock()
        mock_audio_file_context = MagicMock()
        mock_audio_file.return_value = mock_audio_file_context
        mock_audio_file_context.__enter__.return_value = mock_audio_file_instance
        
        # Roep de functie aan
        options = {'language': 'en-US', 'engine': 'sphinx'}
        result = transcribe_with_options("test_audio.wav", options)
        
        # Controleer resultaten
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "This is a test transcription.")
        self.assertEqual(result['engine_used'], 'sphinx')
    
    @patch('modules.file_handler.save_file')
    def test_save_transcription(self, mock_save_file):
        """Test het opslaan van een transcriptie."""
        # Setup mock
        mock_save_file.return_value = "/path/to/test_transcription.txt"
        
        # Roep de functie aan
        text = "Dit is een test transcriptie."
        filename = "test_transcription.txt"
        file_path = save_transcription(text, filename)
        
        # Controleer resultaten
        self.assertEqual(file_path, "/path/to/test_transcription.txt")
        mock_save_file.assert_called_once_with(text, filename)
    
    @patch('modules.file_handler.save_file')
    def test_save_transcription_adds_txt_extension(self, mock_save_file):
        """Test dat .txt extensie wordt toegevoegd als deze ontbreekt."""
        # Setup mock
        mock_save_file.return_value = "/path/to/test_transcription.txt"
        
        # Roep de functie aan
        text = "Dit is een test transcriptie."
        filename = "test_transcription"  # Geen .txt extensie
        save_transcription(text, filename)
        
        # Controleer dat de juiste bestandsnaam met extensie wordt gebruikt
        mock_save_file.assert_called_once_with(text, "test_transcription.txt")
    
    def test_supported_languages(self):
        """Test het ophalen van ondersteunde talen."""
        languages = supported_languages()
        
        # Controleer dat de functie een dictionary teruggeeft
        self.assertIsInstance(languages, dict)
        
        # Controleer dat de belangrijkste talen aanwezig zijn
        self.assertIn('nl-NL', languages)
        self.assertIn('en-US', languages)
        self.assertEqual(languages['nl-NL'], 'Nederlands')
        self.assertEqual(languages['en-US'], 'Engels (VS)')


if __name__ == '__main__':
    unittest.main()
