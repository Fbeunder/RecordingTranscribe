#!/usr/bin/env python3
"""
Transcriber module voor de Record en Transcribe applicatie.

Deze module verzorgt de transcriptie van audiobestanden naar tekst
met behulp van de SpeechRecognition bibliotheek.
"""

import os
import speech_recognition as sr
from typing import Optional, Dict, Any


def transcribe_audio(audio_file: str, language: str = 'nl-NL') -> str:
    """
    Transcribeert een audiobestand naar tekst.
    
    Args:
        audio_file (str): Pad naar het audiobestand
        language (str, optional): Taalcode voor de transcriptie. 
                                  Standaard 'nl-NL' voor Nederlands.
                                  Gebruik 'en-US' voor Engels.
        
    Returns:
        str: De getranscribeerde tekst
        
    Raises:
        FileNotFoundError: Als het audiobestand niet gevonden kan worden
        ValueError: Als het audiobestand niet in een ondersteund formaat is
        Exception: Voor alle andere fouten tijdens transcriptie
    """
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audiobestand niet gevonden: {audio_file}")
    
    # Controleer of het bestand in WAV-formaat is
    if not audio_file.lower().endswith('.wav'):
        raise ValueError("Alleen WAV-bestanden worden ondersteund voor transcriptie")
    
    # Maak een nieuw recognizer object aan
    recognizer = sr.Recognizer()
    
    # Configuratie voor betere spraakherkenning
    recognizer.energy_threshold = 300  # Minimum audio-energie om spraak te detecteren
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # Seconden stilte voordat een zin als compleet wordt beschouwd
    
    try:
        # Open het audiobestand
        with sr.AudioFile(audio_file) as source:
            # Pas noise reduction toe voor betere herkenning
            audio_data = recognizer.record(source)
            
            # Probeer spraak te herkennen met Google Speech Recognition
            # (goed voor zowel Nederlands als Engels)
            text = recognizer.recognize_google(audio_data, language=language)
            return text
    except sr.UnknownValueError:
        # Speech was niet begrijpbaar
        return "Kon geen spraak herkennen in de opname."
    except sr.RequestError as e:
        # API niet bereikbaar of gaf een fout
        raise Exception(f"Kon de spraakherkenningsdienst niet bereiken: {str(e)}")
    except Exception as e:
        # Andere fouten opvangen
        raise Exception(f"Fout tijdens transcriptie: {str(e)}")


def transcribe_with_options(audio_file: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Transcribeert een audiobestand met uitgebreide opties en geeft meer gedetailleerde resultaten.
    
    Args:
        audio_file (str): Pad naar het audiobestand
        options (Dict[str, Any], optional): Opties voor transcriptie:
            - 'language': Taalcode (standaard 'nl-NL')
            - 'engine': Welke engine te gebruiken ('google', 'sphinx', etc.)
            - 'advanced': Boolean of geavanceerde opties gebruikt moeten worden
        
    Returns:
        Dict[str, Any]: Een dictionary met transcriptieresultaten en metadata
    """
    if options is None:
        options = {}
    
    # Standaard opties
    language = options.get('language', 'nl-NL')
    engine = options.get('engine', 'google')
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    result = {
        'success': False,
        'text': '',
        'confidence': 0.0,
        'error': None,
        'engine_used': engine,
        'language': language
    }
    
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            
            # Kies de juiste engine op basis van de options
            if engine == 'sphinx':
                # PocketSphinx werkt offline maar is minder nauwkeurig
                if language.startswith('nl'):
                    # Nederlands is niet standaard ondersteund door PocketSphinx,
                    # val terug op Google als dit beschikbaar is
                    result['text'] = recognizer.recognize_google(audio_data, language=language)
                    result['engine_used'] = 'google (fallback)'
                else:
                    # Voor Engels kunnen we wel PocketSphinx gebruiken
                    result['text'] = recognizer.recognize_sphinx(audio_data)
            else:
                # Gebruik Google (default)
                result['text'] = recognizer.recognize_google(audio_data, language=language)
            
            # Als we hier komen is de transcriptie geslaagd
            result['success'] = True
            
    except sr.UnknownValueError:
        result['error'] = "Kon geen spraak herkennen in de opname"
    except sr.RequestError as e:
        result['error'] = f"Kon de spraakherkenningsdienst niet bereiken: {str(e)}"
    except Exception as e:
        result['error'] = f"Fout tijdens transcriptie: {str(e)}"
    
    return result


def save_transcription(text: str, filename: str) -> str:
    """
    Slaat de transcriptie op als een tekstbestand.
    
    Args:
        text (str): De getranscribeerde tekst
        filename (str): Naam van het bestand waarin de tekst moet worden opgeslagen
        
    Returns:
        str: Pad naar het opgeslagen bestand
        
    Raises:
        Exception: Als het opslaan van de transcriptie mislukt
    """
    from modules.file_handler import save_file
    
    try:
        # Als filename niet eindigt op .txt, voeg het toe
        if not filename.lower().endswith('.txt'):
            filename = f"{filename}.txt"
        
        # Sla het bestand op met de file_handler module
        file_path = save_file(text, filename)
        return file_path
    except Exception as e:
        raise Exception(f"Kon transcriptie niet opslaan: {str(e)}")


def supported_languages() -> Dict[str, str]:
    """
    Geeft een lijst van ondersteunde talen voor transcriptie.
    
    Returns:
        Dict[str, str]: Een dictionary met taalcodes en namen
    """
    return {
        'nl-NL': 'Nederlands',
        'en-US': 'Engels (VS)',
        'en-GB': 'Engels (VK)',
        'de-DE': 'Duits',
        'fr-FR': 'Frans',
        'es-ES': 'Spaans'
    }
