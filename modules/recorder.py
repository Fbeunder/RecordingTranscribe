#!/usr/bin/env python3
"""
Recorder module voor de Record en Transcribe applicatie.

Deze module verzorgt het opnemen van audio via de microfoon met behulp van PyAudio.
Het biedt functionaliteit voor het oplijsten van beschikbare audio-apparaten,
het starten en stoppen van opnames en het opslaan van audio als bestand.
"""

import pyaudio
import wave
import io
import threading
import time
import os
import logging
from typing import List, Dict, Tuple, Optional, Any
from modules.file_handler import save_file

# Configureer logger
logger = logging.getLogger(__name__)

# Globale variabelen voor de opname status
_recording = False
_audio_frames = []
_stream = None
_audio = None
_record_thread = None
_sample_rate = 44100
_channels = 1
_chunk = 1024
_format = pyaudio.paInt16


def list_audio_devices() -> List[Dict[str, Any]]:
    """
    Geeft een lijst van beschikbare audio input-apparaten.
    
    Returns:
        List[Dict[str, Any]]: Een lijst van audio-apparaten met hun eigenschappen
    """
    logger.info("Ophalen van beschikbare audio-apparaten")
    
    try:
        p = pyaudio.PyAudio()
        devices = []
        
        # Itereer over alle beschikbare apparaten
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            
            # Alleen input devices toevoegen (apparaten met min. 1 input kanaal)
            if device_info.get('maxInputChannels', 0) > 0:
                devices.append({
                    'id': i,
                    'name': device_info.get('name', f'Device {i}'),
                    'channels': device_info.get('maxInputChannels', 1)
                })
        
        p.terminate()
        
        logger.info(f"Gevonden audio-apparaten: {len(devices)}")
        
        # Als er geen apparaten zijn gevonden, voeg een standaard apparaat toe
        if not devices:
            logger.warning("Geen apparaten gevonden, gebruik standaard apparaat")
            devices.append({
                'id': 0,
                'name': 'Default Microphone',
                'channels': 1
            })
        
        return devices
    
    except Exception as e:
        logger.error(f"Fout bij ophalen audio-apparaten: {str(e)}")
        # Fallback met standaard apparaat bij fout
        return [{
            'id': 0,
            'name': 'Default Microphone',
            'channels': 1
        }]


def _record_audio():
    """
    Interne functie die audio frames opneemt in een aparte thread.
    """
    global _recording, _audio_frames, _stream
    
    _audio_frames = []
    logger.debug("Start opname thread")
    
    while _recording:
        if _stream:
            try:
                data = _stream.read(_chunk, exception_on_overflow=False)
                _audio_frames.append(data)
            except Exception as e:
                logger.error(f"Fout bij opnemen audio frame: {str(e)}")
                # Stop de opname bij een fout
                _recording = False
                break


def start_recording(device_id: int) -> bool:
    """
    Start een opname met het gekozen apparaat.
    
    Args:
        device_id (int): ID van het gekozen audioapparaat
        
    Returns:
        bool: True als het starten is gelukt
    """
    global _recording, _audio, _stream, _record_thread
    
    logger.info(f"Start opname met apparaat ID: {device_id}")
    
    # Stop eventuele bestaande opname
    if _recording:
        logger.info("Er loopt al een opname, deze wordt eerst gestopt")
        stop_recording()
    
    # Reset opname status
    _recording = True
    _audio_frames.clear()
    
    try:
        # Controleer of het apparaat-ID geldig is
        devices = list_audio_devices()
        valid_device_ids = [device['id'] for device in devices]
        
        if device_id not in valid_device_ids:
            logger.warning(f"Apparaat ID {device_id} niet gevonden, gebruik standaard apparaat (0)")
            device_id = 0  # Fallback naar standaard apparaat
        
        # Initialiseer PyAudio
        _audio = pyaudio.PyAudio()
        
        # Open audio stream
        logger.debug(f"Open audio stream met apparaat {device_id}, samplerate: {_sample_rate}, channels: {_channels}")
        _stream = _audio.open(
            format=_format,
            channels=_channels,
            rate=_sample_rate,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=_chunk
        )
        
        # Start opname in een aparte thread
        _record_thread = threading.Thread(target=_record_audio)
        _record_thread.daemon = True
        _record_thread.start()
        
        logger.info("Opname succesvol gestart")
        return True
    except Exception as e:
        logger.error(f"Fout bij het starten van de opname: {str(e)}")
        _recording = False
        
        # Cleanup
        if _stream:
            try:
                _stream.stop_stream()
                _stream.close()
            except Exception as cleanup_error:
                logger.error(f"Fout bij cleanup van stream: {str(cleanup_error)}")
        
        if _audio:
            try:
                _audio.terminate()
            except Exception as cleanup_error:
                logger.error(f"Fout bij cleanup van PyAudio: {str(cleanup_error)}")
        
        _stream = None
        _audio = None
        
        return False


def stop_recording() -> bytes:
    """
    Stopt de huidige opname.
    
    Returns:
        bytes: Audio data in bytes
    """
    global _recording, _audio_frames, _stream, _audio, _record_thread
    
    if not _recording:
        logger.warning("Er is geen actieve opname om te stoppen")
        return b""
    
    logger.info("Stop opname")
    
    # Stop opname
    _recording = False
    
    # Wacht op de opname thread
    if _record_thread and _record_thread.is_alive():
        logger.debug("Wacht op opname thread om te stoppen")
        _record_thread.join(timeout=1.0)
        if _record_thread.is_alive():
            logger.warning("Opname thread reageert niet, forceer stoppen")
    
    # Sluit stream en PyAudio
    if _stream:
        try:
            logger.debug("Stop en sluit audio stream")
            _stream.stop_stream()
            _stream.close()
            _stream = None
        except Exception as e:
            logger.error(f"Fout bij sluiten van audio stream: {str(e)}")
    
    if _audio:
        try:
            logger.debug("Beëindig PyAudio")
            _audio.terminate()
            _audio = None
        except Exception as e:
            logger.error(f"Fout bij beëindigen van PyAudio: {str(e)}")
    
    # Controleer of er frames zijn opgenomen
    if not _audio_frames:
        logger.warning("Geen audio frames opgenomen")
        return b""
    
    # Log aantal opgenomen frames
    logger.info(f"Aantal opgenomen audio frames: {len(_audio_frames)}")
    
    try:
        # Creëer een in-memory file-like object
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(_channels)
            wf.setsampwidth(pyaudio.get_sample_size(_format))
            wf.setframerate(_sample_rate)
            wf.writeframes(b''.join(_audio_frames))
        
        # Reset audio frames en geef bytes terug
        audio_data = wav_buffer.getvalue()
        frames_count = len(_audio_frames)
        _audio_frames = []
        
        logger.info(f"Opname succesvol gestopt, {len(audio_data)} bytes audio data")
        return audio_data
    except Exception as e:
        logger.error(f"Fout bij verwerken van audio data: {str(e)}")
        _audio_frames = []
        return b""


def save_recording(audio_data: bytes, filename: str) -> str:
    """
    Slaat de opname op als een audiobestand.
    
    Args:
        audio_data (bytes): De audio data in bytes
        filename (str): Naam van het bestand waarin de opname moet worden opgeslagen
        
    Returns:
        str: Pad naar het opgeslagen bestand
        
    Raises:
        ValueError: Als audio_data leeg is
        IOError: Bij fouten in het schrijven naar schijf
    """
    # Controleer of er data is om op te slaan
    if not audio_data or len(audio_data) == 0:
        logger.error("Geen audio data om op te slaan")
        raise ValueError("Geen audio data om op te slaan")
    
    # Zorg ervoor dat de bestandsnaam eindigt op .wav
    if not filename.lower().endswith('.wav'):
        logger.debug(f"Bestandsnaam {filename} heeft geen .wav extensie, wordt toegevoegd")
        filename += '.wav'
    
    try:
        # Gebruik de file_handler module om het bestand op te slaan
        logger.info(f"Opslaan van audio bestand: {filename} ({len(audio_data)} bytes)")
        file_path = save_file(audio_data, filename)
        
        # Controleer of het bestand succesvol is aangemaakt
        if not os.path.exists(file_path):
            logger.error(f"Bestand is niet aangemaakt: {file_path}")
            raise IOError(f"Bestand kon niet worden aangemaakt: {file_path}")
        
        logger.info(f"Audio succesvol opgeslagen als: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Fout bij opslaan van audio: {str(e)}")
        raise IOError(f"Fout bij opslaan van audio: {str(e)}")
