#!/usr/bin/env python3
"""
Tests voor de transcriber module van de Record en Transcribe applicatie.
"""

import unittest
from unittest.mock import patch, MagicMock
from modules.transcriber import transcribe_audio, save_transcription


class TestTranscriber(unittest.TestCase):
    """Test class voor de transcriber module."""
    
    def test_transcribe_audio(self):
        """Test het transcriberen van audio."""
        # TODO: Implementeer deze test
        with patch('speech_recognition.Recognizer'):
            result = transcribe_audio("test_audio.wav")
            self.assertIsInstance(result, str)
    
    def test_save_transcription(self):
        """Test het opslaan van een transcriptie."""
        # TODO: Implementeer deze test
        with patch('modules.file_handler.save_file'):
            text = "Dit is een test transcriptie."
            filename = "test_transcription.txt"
            file_path = save_transcription(text, filename)
            self.assertIsInstance(file_path, str)


if __name__ == '__main__':
    unittest.main()
