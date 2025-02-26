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
from typing import List, Dict, Tuple, Optional, Any
from modules.file_handler import save_file

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
    
    # Als er geen apparaten zijn gevonden, voeg een standaard apparaat toe
    if not devices:
        devices.append({
            'id': 0,
            'name': 'Default Microphone',
            'channels': 1
        })
    
    return devices


def _record_audio():
    """
    Interne functie die audio frames opneemt in een aparte thread.
    """
    global _recording, _audio_frames, _stream
    
    _audio_frames = []
    
    while _recording:
        if _stream:
            try:
                data = _stream.read(_chunk, exception_on_overflow=False)
                _audio_frames.append(data)
            except Exception as e:
                print(f"Fout bij het opnemen: {e}")
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
    
    # Stop eventuele bestaande opname
    if _recording:
        stop_recording()
    
    # Reset opname status
    _recording = True
    _audio_frames.clear()
    
    try:
        # Initialiseer PyAudio
        _audio = pyaudio.PyAudio()
        
        # Open audio stream
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
        
        return True
    except Exception as e:
        print(f"Fout bij het starten van de opname: {e}")
        _recording = False
        
        # Cleanup
        if _stream:
            _stream.stop_stream()
            _stream.close()
        
        if _audio:
            _audio.terminate()
        
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
        return b""
    
    # Stop opname
    _recording = False
    
    # Wacht op de opname thread
    if _record_thread and _record_thread.is_alive():
        _record_thread.join(timeout=1.0)
    
    # Sluit stream en PyAudio
    if _stream:
        _stream.stop_stream()
        _stream.close()
        _stream = None
    
    if _audio:
        _audio.terminate()
        _audio = None
    
    # Converteer frames naar WAV
    if not _audio_frames:
        return b""
    
    # Creëer een in-memory file-like object
    wav_buffer = io.BytesIO()
    
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(_channels)
        wf.setsampwidth(pyaudio.get_sample_size(_format))
        wf.setframerate(_sample_rate)
        wf.writeframes(b''.join(_audio_frames))
    
    # Reset audio frames en geef bytes terug
    audio_data = wav_buffer.getvalue()
    _audio_frames = []
    
    return audio_data


def save_recording(audio_data: bytes, filename: str) -> str:
    """
    Slaat de opname op als een audiobestand.
    
    Args:
        audio_data (bytes): De audio data in bytes
        filename (str): Naam van het bestand waarin de opname moet worden opgeslagen
        
    Returns:
        str: Pad naar het opgeslagen bestand
    """
    # Zorg ervoor dat de bestandsnaam eindigt op .wav
    if not filename.lower().endswith('.wav'):
        filename += '.wav'
    
    # Gebruik de file_handler module om het bestand op te slaan
    return save_file(audio_data, filename)
