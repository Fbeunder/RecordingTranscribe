#!/usr/bin/env python3
"""
Transcriber module voor de Record en Transcribe applicatie.

Deze module verzorgt de transcriptie van audiobestanden naar tekst
met behulp van de SpeechRecognition bibliotheek.
"""

import os
import logging
import speech_recognition as sr
from typing import Optional, Dict, Any, List, Tuple
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
            
            # Als 'auto' is meegegeven voor taal, probeer de taal automatisch te detecteren
            if language == 'auto':
                language, confidence = detect_language(audio_data, recognizer)
                logger.info(f"Taal automatisch gedetecteerd: {language} (betrouwbaarheid: {confidence:.2f})")
            
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


def detect_language(audio_data, recognizer) -> Tuple[str, float]:
    """
    Detecteert de taal van het audiobestand.
    
    Args:
        audio_data: Audio data van het bestand
        recognizer: SpeechRecognition recognizer object
        
    Returns:
        Tuple[str, float]: Gedetecteerde taalcode en betrouwbaarheidsscore (0-1)
    """
    # Lijst van talen om te testen in volgorde van populariteit in NL
    test_languages = [
        'nl-NL',  # Nederlands
        'en-US',  # Engels (VS)
        'en-GB',  # Engels (VK)
        'de-DE',  # Duits
        'fr-FR',  # Frans
        'es-ES',  # Spaans
        'it-IT',  # Italiaans
        'tr-TR',  # Turks
        'ar-SA',  # Arabisch
        'pl-PL'   # Pools
    ]
    
    best_score = 0.0
    detected_language = 'nl-NL'  # Standaard terugvallen op Nederlands
    
    try:
        # Probeer om een stukje tekst te herkennen in elke taal
        for lang in test_languages:
            try:
                # Probeer een deel van de audio te transcriberen in deze taal
                logger.debug(f"Probeer taaldetectie met {lang}")
                text = recognizer.recognize_google(audio_data, language=lang, show_all=True)
                
                # De resultaten bevatten een betrouwbaarheidsscore als het herkennen is gelukt
                if isinstance(text, dict) and 'alternative' in text:
                    # Pak de beste match en de bijbehorende betrouwbaarheidsscore
                    alternatives = text['alternative']
                    if alternatives and 'confidence' in alternatives[0]:
                        confidence = float(alternatives[0]['confidence'])
                        
                        # Als de betrouwbaarheid hoger is dan wat we tot nu toe hebben gevonden
                        if confidence > best_score:
                            best_score = confidence
                            detected_language = lang
                            logger.debug(f"Betere taalovereenkomst gevonden: {lang} met score {confidence}")
                            
                            # Als de score heel hoog is, ga dan direct verder
                            if confidence > 0.8:
                                break
            except Exception as e:
                # Negeer fouten bij een enkele taal en ga door met de volgende
                logger.debug(f"Fout bij detecteren van taal {lang}: {str(e)}")
                continue
    except Exception as e:
        logger.warning(f"Kon taal niet detecteren: {str(e)}")
        # Terugvallen op Nederlands bij problemen
    
    return detected_language, best_score


def transcribe_with_options(audio_file: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Transcribeert een audiobestand met uitgebreide opties en geeft meer gedetailleerde resultaten.
    
    Args:
        audio_file (str): Pad naar het audiobestand
        options (Dict[str, Any], optional): Opties voor transcriptie:
            - 'language': Taalcode (standaard 'nl-NL') of 'auto' voor automatische detectie
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
    detect_lang = options.get('detect_language', False)
    
    # Als automatische taaldetectie is ingeschakeld
    if detect_lang or language == 'auto':
        language = 'auto'
    # Anders controleer of de opgegeven taal wordt ondersteund
    else:
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
        'detected_language': None,
        'language_confidence': 0.0,
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
            
            # Automatische taaldetectie indien nodig
            if language == 'auto':
                detected_lang, confidence = detect_language(audio_data, recognizer)
                result['detected_language'] = detected_lang
                result['language_confidence'] = confidence
                result['language'] = detected_lang
                language = detected_lang
                logger.info(f"Taal automatisch gedetecteerd: {language} (betrouwbaarheid: {confidence:.2f})")
            
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
                text_result = recognizer.recognize_google(audio_data, language=language, show_all=True)
                
                # Probeer om betrouwbaarheidsscore te extraheren
                if isinstance(text_result, dict) and 'alternative' in text_result and text_result['alternative']:
                    alternatives = text_result['alternative']
                    result['text'] = alternatives[0]['transcript']
                    if 'confidence' in alternatives[0]:
                        result['confidence'] = float(alternatives[0]['confidence'])
                else:
                    # Fallback wanneer show_all=True niet werkt
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
        # Europese talen
        'nl-NL': 'Nederlands',
        'en-US': 'Engels (VS)',
        'en-GB': 'Engels (VK)',
        'en-AU': 'Engels (Australië)',
        'en-IN': 'Engels (India)',
        'de-DE': 'Duits',
        'fr-FR': 'Frans',
        'es-ES': 'Spaans (Spanje)',
        'es-MX': 'Spaans (Mexico)',
        'it-IT': 'Italiaans',
        'pt-PT': 'Portugees (Portugal)',
        'pt-BR': 'Portugees (Brazilië)',
        'ru-RU': 'Russisch',
        'pl-PL': 'Pools',
        'sv-SE': 'Zweeds',
        'no-NO': 'Noors',
        'da-DK': 'Deens',
        'fi-FI': 'Fins',
        'uk-UA': 'Oekraïens',
        'el-GR': 'Grieks',
        'hu-HU': 'Hongaars',
        'cs-CZ': 'Tsjechisch',
        'sk-SK': 'Slowaaks',
        'ro-RO': 'Roemeens',
        'bg-BG': 'Bulgaars',
        'hr-HR': 'Kroatisch',
        'sr-RS': 'Servisch',
        'sl-SI': 'Sloveens',
        
        # Aziatische talen
        'ja-JP': 'Japans',
        'zh-CN': 'Chinees (Vereenvoudigd)',
        'zh-TW': 'Chinees (Traditioneel)',
        'ko-KR': 'Koreaans',
        'th-TH': 'Thais',
        'vi-VN': 'Vietnamees',
        'id-ID': 'Indonesisch',
        'ms-MY': 'Maleis',
        'hi-IN': 'Hindi',
        'bn-IN': 'Bengaals',
        'ta-IN': 'Tamil',
        'ur-PK': 'Urdu',
        
        # Midden-Oosten en Afrikaanse talen
        'ar-AE': 'Arabisch (VAE)',
        'ar-SA': 'Arabisch (Saoedi-Arabië)',
        'fa-IR': 'Perzisch',
        'tr-TR': 'Turks',
        'he-IL': 'Hebreeuws',
        'af-ZA': 'Afrikaans',
        'zu-ZA': 'Zoeloe',
        'sw-KE': 'Swahili',
        
        # Speciale waarde voor automatische taaldetectie
        'auto': 'Automatisch detecteren'
    }


def get_popular_languages() -> Dict[str, str]:
    """
    Geeft een lijst van populaire talen die in Nederland veel voorkomen.
    Handig voor het tonen van een kortere lijst in de interface.
    
    Returns:
        Dict[str, str]: Een dictionary met taalcodes en namen van populaire talen
    """
    return {
        'nl-NL': 'Nederlands',
        'en-US': 'Engels (VS)',
        'en-GB': 'Engels (VK)',
        'de-DE': 'Duits',
        'fr-FR': 'Frans',
        'es-ES': 'Spaans',
        'tr-TR': 'Turks',
        'ar-SA': 'Arabisch',
        'pl-PL': 'Pools',
        'auto': 'Automatisch detecteren'
    }


def get_language_groups() -> Dict[str, Dict[str, str]]:
    """
    Geeft talen gegroepeerd per regio.
    Handig voor het organiseren van talen in een georganiseerde interface.
    
    Returns:
        Dict[str, Dict[str, str]]: Een dictionary met regio's en bijbehorende talen
    """
    all_languages = supported_languages()
    
    return {
        "Populair": get_popular_languages(),
        "Europa": {k: v for k, v in all_languages.items() if k in [
            'nl-NL', 'en-US', 'en-GB', 'de-DE', 'fr-FR', 'es-ES', 'it-IT', 
            'pt-PT', 'ru-RU', 'pl-PL', 'sv-SE', 'no-NO', 'da-DK', 'fi-FI',
            'uk-UA', 'el-GR', 'hu-HU', 'cs-CZ', 'sk-SK', 'ro-RO', 'bg-BG',
            'hr-HR', 'sr-RS', 'sl-SI'
        ]},
        "Azië": {k: v for k, v in all_languages.items() if k in [
            'ja-JP', 'zh-CN', 'zh-TW', 'ko-KR', 'th-TH', 'vi-VN', 'id-ID',
            'ms-MY', 'hi-IN', 'bn-IN', 'ta-IN', 'ur-PK'
        ]},
        "Midden-Oosten & Afrika": {k: v for k, v in all_languages.items() if k in [
            'ar-AE', 'ar-SA', 'fa-IR', 'tr-TR', 'he-IL', 'af-ZA', 'zu-ZA', 'sw-KE'
        ]},
        "Amerika's": {k: v for k, v in all_languages.items() if k in [
            'en-US', 'es-MX', 'pt-BR'
        ]},
        "Oceanië": {k: v for k, v in all_languages.items() if k in [
            'en-AU'
        ]},
        "Speciale opties": {
            'auto': 'Automatisch detecteren'
        }
    }


def get_supported_audio_formats() -> List[str]:
    """
    Geeft een lijst van ondersteunde audioformaten voor transcriptie.
    
    Returns:
        List[str]: Lijst met ondersteunde bestandsextensies
    """
    from modules.file_handler import SUPPORTED_AUDIO_EXTENSIONS
    return SUPPORTED_AUDIO_EXTENSIONS
