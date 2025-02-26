#!/usr/bin/env python3
"""
File handler module voor de Record en Transcribe applicatie.

Deze module verzorgt het bestandsbeheer voor opnames en transcripties.
Het biedt functionaliteit voor het bepalen van de download map,
het opslaan van bestanden en het laden van bestanden.
"""

import os
import time
import logging
import shutil
import tempfile
from typing import Union, Optional, List, Tuple, Dict

# Configureer logger
logger = logging.getLogger(__name__)

# Constanten voor bestandsvalidatie
SUPPORTED_AUDIO_EXTENSIONS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
SUPPORTED_AUDIO_MIMETYPES = [
    'audio/wav', 'audio/x-wav', 'audio/wave',
    'audio/mpeg', 'audio/mp3',
    'audio/mp4', 'audio/x-m4a',
    'audio/flac', 'audio/x-flac',
    'audio/ogg', 'application/ogg',
    'audio/aac', 'audio/x-aac'
]
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB als maximale uploadgrootte

def get_download_folder() -> str:
    """
    Bepaalt de standaard download-map van de browser.
    
    Returns:
        str: Pad naar de download-map
    """
    # In een webapplicatie wordt dit meestal geregeld door de browser
    # en niet door de server. Voor nu gebruiken we een relatief pad.
    download_folder = os.path.join(os.getcwd(), "downloads")
    
    try:
        # Maak de map aan als deze nog niet bestaat
        if not os.path.exists(download_folder):
            logger.info(f"Aanmaken van download map: {download_folder}")
            os.makedirs(download_folder)
        
        # Controleer of we schrijfrechten hebben in de map
        test_file = os.path.join(download_folder, ".write_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        logger.info(f"Download map gecontroleerd en in orde: {download_folder}")
        return download_folder
    
    except PermissionError:
        logger.error(f"Geen schrijfrechten in map: {download_folder}")
        # Probeer een tijdelijke map als fallback
        fallback = os.path.join(os.path.expanduser("~"), "temp_recordings")
        logger.warning(f"Gebruik fallback map: {fallback}")
        
        if not os.path.exists(fallback):
            os.makedirs(fallback)
        
        return fallback
    
    except Exception as e:
        logger.error(f"Fout bij bepalen download map: {str(e)}")
        # Fallback naar temp directory
        temp_dir = os.path.join(os.path.expanduser("~"), "temp_recordings")
        logger.warning(f"Gebruik temp map als fallback: {temp_dir}")
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        return temp_dir


def save_file(data: Union[bytes, str], filename: str, folder: Optional[str] = None) -> str:
    """
    Slaat data op als een bestand.
    
    Args:
        data (bytes of str): De data die moet worden opgeslagen
        filename (str): Naam van het bestand
        folder (str, optioneel): Map waarin het bestand moet worden opgeslagen
        
    Returns:
        str: Volledig pad naar het opgeslagen bestand
        
    Raises:
        ValueError: Als de data of bestandsnaam ongeldig is
        IOError: Bij fouten in het schrijven naar schijf
    """
    # Valideer input parameters
    if not data:
        logger.error("Poging om leeg bestand op te slaan")
        raise ValueError("Kan geen leeg bestand opslaan")
    
    if not filename or not isinstance(filename, str):
        logger.error(f"Ongeldige bestandsnaam: {filename}")
        raise ValueError("Bestandsnaam moet een geldige string zijn")
    
    # Gebruik de opgegeven map of de standaard download map
    if folder is None:
        folder = get_download_folder()
    
    try:
        # Zorg ervoor dat de map bestaat
        if not os.path.exists(folder):
            logger.info(f"Aanmaken van map: {folder}")
            os.makedirs(folder)
        
        # Voeg tijdstempel toe aan bestandsnaam om overschrijven te voorkomen
        name, ext = os.path.splitext(filename)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        unique_filename = f"{name}_{timestamp}{ext}"
        
        filepath = os.path.join(folder, unique_filename)
        
        # Log informatie voor debug doeleinden
        if isinstance(data, bytes):
            logger.info(f"Opslaan binair bestand ({len(data)} bytes): {filepath}")
        else:
            logger.info(f"Opslaan tekstbestand ({len(data)} tekens): {filepath}")
        
        # Sla het bestand op
        mode = 'wb' if isinstance(data, bytes) else 'w'
        with open(filepath, mode) as f:
            f.write(data)
        
        # Controleer of het bestand succesvol is aangemaakt
        if not os.path.exists(filepath):
            logger.error(f"Bestand kon niet worden aangemaakt: {filepath}")
            raise IOError(f"Bestand kon niet worden aangemaakt: {filepath}")
        
        file_size = os.path.getsize(filepath)
        logger.info(f"Bestand succesvol opgeslagen: {filepath} ({file_size} bytes)")
        
        return filepath
    
    except PermissionError as e:
        logger.error(f"Geen schrijfrechten voor: {folder}")
        raise IOError(f"Geen toestemming om te schrijven naar: {folder}")
    
    except Exception as e:
        logger.error(f"Fout bij opslaan van bestand: {str(e)}")
        raise IOError(f"Kon bestand niet opslaan: {str(e)}")


def load_file(filepath: str) -> Union[bytes, str]:
    """
    Laadt een bestand van schijf.
    
    Args:
        filepath (str): Pad naar het bestand
        
    Returns:
        bytes of str: Inhoud van het bestand
        
    Raises:
        FileNotFoundError: Als het bestand niet gevonden kan worden
        IOError: Bij fouten in het lezen van het bestand
    """
    if not filepath or not isinstance(filepath, str):
        logger.error(f"Ongeldig bestandspad: {filepath}")
        raise ValueError("Bestandspad moet een geldige string zijn")
    
    if not os.path.exists(filepath):
        logger.error(f"Bestand niet gevonden: {filepath}")
        raise FileNotFoundError(f"Bestand niet gevonden: {filepath}")
    
    # Detecteer of het een tekstbestand of binair bestand is op basis van extensie
    ext = os.path.splitext(filepath)[1].lower()
    text_extensions = ['.txt', '.json', '.csv', '.md', '.html', '.xml']
    
    try:
        file_size = os.path.getsize(filepath)
        logger.info(f"Laden van bestand: {filepath} ({file_size} bytes)")
        
        if ext in text_extensions:
            # Tekstbestand
            logger.debug(f"Bestand wordt geladen als tekst: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"Tekstbestand geladen: {filepath} ({len(content)} tekens)")
                return content
        else:
            # Binair bestand
            logger.debug(f"Bestand wordt geladen als binair: {filepath}")
            with open(filepath, 'rb') as f:
                content = f.read()
                logger.info(f"Binair bestand geladen: {filepath} ({len(content)} bytes)")
                return content
    
    except UnicodeDecodeError as e:
        logger.error(f"Kan bestand niet decoderen als tekst, probeer binair: {filepath}")
        # Als we een decodering error krijgen, probeer het als binair bestand
        with open(filepath, 'rb') as f:
            content = f.read()
            logger.info(f"Binair bestand geladen (fallback): {filepath} ({len(content)} bytes)")
            return content
    
    except Exception as e:
        logger.error(f"Fout bij laden van bestand: {str(e)}")
        raise IOError(f"Kon bestand niet laden: {str(e)}")


def validate_audio_file(file: Union[str, bytes], filename: str) -> Tuple[bool, Optional[str]]:
    """
    Valideert of een bestand een geldig en ondersteund audiobestand is.
    
    Args:
        file (str of bytes): Bestandspad of bestandsinhoud
        filename (str): Bestandsnaam (voor extensiecontrole)
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Controleer de extensie
    _, ext = os.path.splitext(filename.lower())
    
    if not ext:
        return False, "Bestand heeft geen extensie"
    
    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        return False, f"Bestandsextensie {ext} wordt niet ondersteund. Ondersteunde extensies: {', '.join(SUPPORTED_AUDIO_EXTENSIONS)}"
    
    # Als file een string is (pad), controleer bestandsgrootte
    if isinstance(file, str):
        if not os.path.exists(file):
            return False, "Bestand bestaat niet"
        
        file_size = os.path.getsize(file)
        if file_size > MAX_UPLOAD_SIZE:
            max_size_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
            return False, f"Bestand is te groot ({file_size / (1024 * 1024):.2f} MB). Maximale grootte is {max_size_mb} MB"
        
        if file_size == 0:
            return False, "Bestand is leeg"
    
    # Als file bytes zijn, controleer alleen de bestandsgrootte
    elif isinstance(file, bytes):
        if len(file) > MAX_UPLOAD_SIZE:
            max_size_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
            return False, f"Bestand is te groot ({len(file) / (1024 * 1024):.2f} MB). Maximale grootte is {max_size_mb} MB"
        
        if len(file) == 0:
            return False, "Bestand is leeg"
    
    # Bestand is geldig
    return True, None


def convert_audio_to_wav(input_file: str) -> str:
    """
    Converteert een audiobestand naar WAV-formaat (indien nodig).
    
    Args:
        input_file (str): Pad naar het invoerbestand
    
    Returns:
        str: Pad naar het geconverteerde WAV-bestand
    
    Raises:
        ValueError: Als het bestand niet kan worden geconverteerd
        IOError: Bij fouten in het converteren
    """
    # Als het bestand al een WAV-bestand is, return het pad
    if input_file.lower().endswith('.wav'):
        logger.info(f"Bestand is al in WAV-formaat: {input_file}")
        return input_file
    
    try:
        # We gebruiken pydub om de conversie uit te voeren
        from pydub import AudioSegment
        
        # Bepaal het bestandsformaat op basis van de extensie
        _, ext = os.path.splitext(input_file.lower())
        ext = ext[1:]  # Verwijder de punt
        
        # Bepaal het uitvoerbestand en bestandsformaat
        output_file = os.path.join(tempfile.gettempdir(), f"{os.path.basename(input_file)}.wav")
        
        # Laad het audiobestand met pydub (format is automatisch afgeleid van extensie)
        logger.info(f"Start conversie van {ext} naar WAV: {input_file}")
        
        # MP3 naar WAV
        if ext == 'mp3':
            audio = AudioSegment.from_mp3(input_file)
        # OGG naar WAV
        elif ext == 'ogg':
            audio = AudioSegment.from_ogg(input_file)
        # FLAC naar WAV
        elif ext == 'flac':
            audio = AudioSegment.from_file(input_file, format="flac")
        # AAC/M4A naar WAV
        elif ext in ['aac', 'm4a']:
            audio = AudioSegment.from_file(input_file, format=ext)
        else:
            # Generieke conversie voor niet-specifiek ondersteunde formaten
            audio = AudioSegment.from_file(input_file)
        
        # Exporteer naar WAV
        audio.export(output_file, format="wav")
        
        # Controleer of het bestand succesvol is aangemaakt
        if not os.path.exists(output_file):
            logger.error(f"Geconverteerd bestand kon niet worden aangemaakt: {output_file}")
            raise IOError(f"Geconverteerd bestand kon niet worden aangemaakt: {output_file}")
        
        file_size = os.path.getsize(output_file)
        logger.info(f"Bestand succesvol geconverteerd naar WAV: {output_file} ({file_size} bytes)")
        
        return output_file
        
    except ImportError as e:
        logger.error(f"Bibliotheek voor audioconversie ontbreekt: {str(e)}")
        raise ValueError(f"Kan bestand niet converteren: vereiste module ontbreekt ({str(e)})")
    
    except Exception as e:
        logger.error(f"Fout bij converteren naar WAV: {str(e)}")
        raise IOError(f"Kon bestand niet converteren naar WAV: {str(e)}")


def get_supported_audio_info() -> Dict[str, List[str]]:
    """
    Geeft informatie over ondersteunde audioformaten.
    
    Returns:
        Dict[str, List[str]]: Dictionary met ondersteunde extensies en MIME-types
    """
    return {
        'extensions': SUPPORTED_AUDIO_EXTENSIONS,
        'mime_types': SUPPORTED_AUDIO_MIMETYPES,
        'max_size': MAX_UPLOAD_SIZE
    }
