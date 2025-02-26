#!/usr/bin/env python3
"""
Transcriber module voor de Record en Transcribe applicatie.

Deze module verzorgt de transcriptie van audiobestanden naar tekst
met behulp van de SpeechRecognition bibliotheek.
"""

import os
import logging
import speech_recognition as sr
from typing import Optional, Dict, Any, List
from modules.file_handler import convert_audio_to_wav

# Configureer logger
logger = logging.getLogger(__name__)

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
        ValueError: Als het audiobestand niet in een ondersteund formaat is of als de taal niet ondersteund wordt
        Exception: Voor alle andere fouten tijdens transcriptie
    """
    # Controleer of de opgegeven taal wordt ondersteund
    supported = supported_languages()
    if language not in supported:
        logger.warning(f"Niet-ondersteunde taal opgegeven: {language}, terugvallen op nl-NL")
        language = 'nl-NL'  # Terugvallen op Nederlands
    
    if not os.path.exists(audio_file):
        logger.error(f"Audiobestand niet gevonden: {audio_file}")
        raise FileNotFoundError(f"Audiobestand niet gevonden: {audio_file}")
    
    # Controleer of het bestand een ondersteund formaat heeft en converteer indien nodig
    try:
        # Als het geen WAV-bestand is, converteer het naar WAV
        if not audio_file.lower().endswith('.wav'):
            logger.info(f"Converteer niet-WAV bestand naar WAV: {audio_file}")
            wav_file = convert_audio_to_wav(audio_file)
            logger.info(f"Bestand geconverteerd naar WAV: {wav_file}")
        else:
            wav_file = audio_file
        
        # Maak een nieuw recognizer object aan
        recognizer = sr.Recognizer()
        
        # Configuratie voor betere spraakherkenning
        recognizer.energy_threshold = 300  # Minimum audio-energie om spraak te detecteren
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8  # Seconden stilte voordat een zin als compleet wordt beschouwd
        
        # Open het audiobestand
        with sr.AudioFile(wav_file) as source:
            # Pas noise reduction toe voor betere herkenning
            audio_data = recognizer.record(source)
            
            # Probeer spraak te herkennen met Google Speech Recognition
            logger.info(f"Start transcriptie met Google Speech Recognition in taal: {language}")
            text = recognizer.recognize_google(audio_data, language=language)
            logger.info(f"Transcriptie succesvol: {len(text)} karakters")
            
            # Als het bestand is geconverteerd en niet het originele bestand is, 
            # verwijder het tijdelijke bestand
            if wav_file != audio_file and os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                    logger.info(f"Tijdelijk WAV-bestand verwijderd: {wav_file}")
                except Exception as e:
                    logger.warning(f"Kon tijdelijk WAV-bestand niet verwijderen: {str(e)}")
            
            return text
    except sr.UnknownValueError:
        # Speech was niet begrijpbaar
        logger.warning(f"Geen spraak herkend in bestand: {audio_file}")
        return "Kon geen spraak herkennen in de opname."
    except sr.RequestError as e:
        # API niet bereikbaar of gaf een fout
        logger.error(f"Google Speech Recognition service niet bereikbaar: {str(e)}")
        raise Exception(f"Kon de spraakherkenningsdienst niet bereiken: {str(e)}")
    except ValueError as e:
        # Probleem met validatie of conversie
        logger.error(f"Validatie of conversie fout: {str(e)}")
        raise ValueError(f"Probleem met audiobestand: {str(e)}")
    except Exception as e:
        # Andere fouten opvangen
        logger.error(f"Fout tijdens transcriptie: {str(e)}")
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
        
    Raises:
        ValueError: Als het audiobestand niet in een ondersteund formaat is of als de taal niet ondersteund wordt
    """
    if options is None:
        options = {}
    
    # Standaard opties
    language = options.get('language', 'nl-NL')
    engine = options.get('engine', 'google')
    
    # Controleer of de opgegeven taal wordt ondersteund
    supported = supported_languages()
    if language not in supported:
        logger.warning(f"Niet-ondersteunde taal opgegeven: {language}, terugvallen op nl-NL")
        language = 'nl-NL'  # Terugvallen op Nederlands
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    result = {
        'success': False,
        'text': '',
        'confidence': 0.0,
        'error': None,
        'engine_used': engine,
        'language': language,
        'original_file': audio_file,
        'converted': False
    }
    
    # Controleer of het bestand bestaat
    if not os.path.exists(audio_file):
        result['error'] = f"Audiobestand niet gevonden: {audio_file}"
        return result
    
    # Converteer het bestand indien nodig
    try:
        # Als het geen WAV-bestand is, converteer het naar WAV
        if not audio_file.lower().endswith('.wav'):
            logger.info(f"Converteer niet-WAV bestand naar WAV voor geavanceerde transcriptie: {audio_file}")
            wav_file = convert_audio_to_wav(audio_file)
            logger.info(f"Bestand geconverteerd naar WAV: {wav_file}")
            result['converted'] = True
        else:
            wav_file = audio_file
        
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            
            # Kies de juiste engine op basis van de options
            if engine == 'sphinx':
                # PocketSphinx werkt offline maar is minder nauwkeurig
                if language.startswith('nl'):
                    # Nederlands is niet standaard ondersteund door PocketSphinx,
                    # val terug op Google als dit beschikbaar is
                    logger.info(f"PocketSphinx ondersteunt geen Nederlands, gebruik Google (fallback)")
                    result['text'] = recognizer.recognize_google(audio_data, language=language)
                    result['engine_used'] = 'google (fallback)'
                else:
                    # Voor Engels kunnen we wel PocketSphinx gebruiken
                    logger.info(f"Gebruik PocketSphinx voor transcriptie")
                    result['text'] = recognizer.recognize_sphinx(audio_data)
            else:
                # Gebruik Google (default)
                logger.info(f"Gebruik Google Speech Recognition voor transcriptie in taal: {language}")
                result['text'] = recognizer.recognize_google(audio_data, language=language)
            
            # Als we hier komen is de transcriptie geslaagd
            logger.info(f"Transcriptie succesvol met {result['engine_used']}: {len(result['text'])} karakters")
            result['success'] = True
            
            # Schoon tijdelijke bestanden op
            if result['converted'] and wav_file != audio_file and os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                    logger.info(f"Tijdelijk WAV-bestand verwijderd: {wav_file}")
                except Exception as e:
                    logger.warning(f"Kon tijdelijk WAV-bestand niet verwijderen: {str(e)}")
            
    except sr.UnknownValueError:
        logger.warning(f"Geen spraak herkend in bestand: {audio_file}")
        result['error'] = "Kon geen spraak herkennen in de opname"
    except sr.RequestError as e:
        logger.error(f"Spraakherkenningsdienst niet bereikbaar: {str(e)}")
        result['error'] = f"Kon de spraakherkenningsdienst niet bereiken: {str(e)}"
    except ValueError as e:
        logger.error(f"Validatie of conversie fout: {str(e)}")
        result['error'] = f"Probleem met audiobestand: {str(e)}"
    except Exception as e:
        logger.error(f"Fout tijdens transcriptie: {str(e)}")
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
        
        logger.info(f"Opslaan van transcriptie als: {filename}")
        
        # Sla het bestand op met de file_handler module
        file_path = save_file(text, filename)
        logger.info(f"Transcriptie succesvol opgeslagen als: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Kon transcriptie niet opslaan: {str(e)}")
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
        'es-ES': 'Spaans',
        'it-IT': 'Italiaans',
        'pt-PT': 'Portugees (Portugal)',
        'pt-BR': 'Portugees (Brazilië)',
        'ru-RU': 'Russisch',
        'ja-JP': 'Japans',
        'zh-CN': 'Chinees (Vereenvoudigd)',
        'ko-KR': 'Koreaans'
    }


def get_supported_audio_formats() -> List[str]:
    """
    Geeft een lijst van ondersteunde audioformaten voor transcriptie.
    
    Returns:
        List[str]: Lijst met ondersteunde bestandsextensies
    """
    from modules.file_handler import SUPPORTED_AUDIO_EXTENSIONS
    return SUPPORTED_AUDIO_EXTENSIONS
