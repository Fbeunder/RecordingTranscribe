#!/usr/bin/env python3
"""
Web interface module voor de Record en Transcribe applicatie.

Deze module verzorgt de web-GUI en API-endpoints met behulp van Flask.
Het registreert routes en API-endpoints, en zorgt voor de communicatie
tussen de gebruiker en de backend functionaliteit.
"""

from flask import render_template, request, jsonify, send_file, current_app
from modules.recorder import list_audio_devices, start_recording, stop_recording, save_recording
from modules.transcriber import transcribe_audio, save_transcription
from modules.file_handler import get_download_folder


def init_app(app):
    """
    Initialiseert de Flask routes en API endpoints.
    
    Args:
        app: Flask app instance
    """
    @app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')
    
    @app.route('/api/devices', methods=['GET'])
    def get_devices():
        """API endpoint om beschikbare audio-apparaten op te halen."""
        # TODO: Implementeer het ophalen van beschikbare audio-apparaten
        devices = []
        try:
            devices = list_audio_devices()
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        return jsonify({'devices': devices})
    
    @app.route('/api/record/start', methods=['POST'])
    def api_start_recording():
        """API endpoint om een opname te starten."""
        # TODO: Implementeer het starten van een opname
        data = request.get_json()
        device_id = data.get('device_id', 0)  # Default naar device 0 als niet opgegeven
        
        try:
            success = start_recording(device_id)
            if success:
                return jsonify({'status': 'recording'})
            else:
                return jsonify({'error': 'Kon opname niet starten'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/record/stop', methods=['POST'])
    def api_stop_recording():
        """API endpoint om een opname te stoppen."""
        # TODO: Implementeer het stoppen van een opname
        try:
            audio_data = stop_recording()
            filename = "recording.wav"
            file_path = save_recording(audio_data, filename)
            
            return jsonify({
                'status': 'stopped',
                'filename': filename,
                'file_path': file_path
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/transcribe', methods=['POST'])
    def api_transcribe():
        """API endpoint om een audio bestand te transcriberen."""
        # TODO: Implementeer het transcriberen van een audiobestand
        data = request.get_json()
        audio_file = data.get('audio_file')
        
        try:
            if audio_file:
                text = transcribe_audio(audio_file)
                filename = audio_file.replace('.wav', '.txt')
                file_path = save_transcription(text, filename)
                
                return jsonify({
                    'text': text,
                    'filename': filename,
                    'file_path': file_path
                })
            else:
                return jsonify({'error': 'Geen audiobestand opgegeven'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
