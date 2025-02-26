#!/usr/bin/env python3
"""
Web interface module voor de Record en Transcribe applicatie.

Deze module verzorgt de web-GUI en API-endpoints met behulp van Flask.
Het registreert routes en API-endpoints, en zorgt voor de communicatie
tussen de gebruiker en de backend functionaliteit.
"""

import os
import logging
from flask import render_template, request, jsonify, send_file, current_app
from modules.recorder import list_audio_devices, start_recording, stop_recording, save_recording
from modules.transcriber import transcribe_audio, save_transcription, supported_languages
from modules.file_handler import get_download_folder

# Configureer logging
logger = logging.getLogger(__name__)

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
        try:
            devices = list_audio_devices()
            logger.info(f"Gevonden audio apparaten: {len(devices)}")
            return jsonify({'devices': devices})
        except Exception as e:
            logger.error(f"Fout bij ophalen audio apparaten: {str(e)}")
            return jsonify({
                'error': 'Kon audio apparaten niet ophalen',
                'details': str(e)
            }), 500
    
    @app.route('/api/record/start', methods=['POST'])
    def api_start_recording():
        """API endpoint om een opname te starten."""
        try:
            data = request.get_json()
            if data is None:
                logger.warning("Geen JSON data ontvangen bij start_recording")
                return jsonify({'error': 'Geen geldige JSON data ontvangen'}), 400
            
            device_id = data.get('device_id', 0)  # Default naar device 0 als niet opgegeven
            logger.info(f"Start opname met apparaat ID: {device_id}")
            
            success = start_recording(device_id)
            if success:
                logger.info("Opname succesvol gestart")
                return jsonify({'status': 'recording', 'device_id': device_id})
            else:
                logger.error(f"Kon opname niet starten met apparaat ID: {device_id}")
                return jsonify({
                    'error': 'Kon opname niet starten',
                    'details': f'Apparaat {device_id} kan mogelijk niet worden gebruikt'
                }), 500
        except ValueError as e:
            logger.error(f"Ongeldige waarde bij start_recording: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Onverwachte fout bij start_recording: {str(e)}")
            return jsonify({
                'error': 'Kon opname niet starten',
                'details': str(e)
            }), 500
    
    @app.route('/api/record/stop', methods=['POST'])
    def api_stop_recording():
        """API endpoint om een opname te stoppen."""
        try:
            logger.info("Stop opname")
            audio_data = stop_recording()
            
            if not audio_data or len(audio_data) == 0:
                logger.warning("Geen audio data ontvangen bij stoppen opname")
                return jsonify({
                    'error': 'Geen audio data ontvangen',
                    'details': 'De opname bevat mogelijk geen audio'
                }), 400
            
            filename = "recording.wav"
            file_path = save_recording(audio_data, filename)
            logger.info(f"Opname opgeslagen als: {file_path}")
            
            return jsonify({
                'status': 'stopped',
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': len(audio_data)
            })
        except FileNotFoundError as e:
            logger.error(f"Bestand niet gevonden: {str(e)}")
            return jsonify({
                'error': 'Bestand niet gevonden',
                'details': str(e)
            }), 404
        except PermissionError as e:
            logger.error(f"Geen schrijfrechten: {str(e)}")
            return jsonify({
                'error': 'Geen schrijfrechten',
                'details': str(e)
            }), 403
        except Exception as e:
            logger.error(f"Fout bij stoppen opname: {str(e)}")
            return jsonify({
                'error': 'Kon opname niet stoppen of opslaan',
                'details': str(e)
            }), 500
    
    @app.route('/api/transcribe', methods=['POST'])
    def api_transcribe():
        """API endpoint om een audio bestand te transcriberen."""
        try:
            data = request.get_json()
            if data is None:
                logger.warning("Geen JSON data ontvangen bij transcribe")
                return jsonify({'error': 'Geen geldige JSON data ontvangen'}), 400
            
            audio_file = data.get('audio_file')
            language = data.get('language', 'nl-NL')  # Default taal is Nederlands
            
            if not audio_file:
                logger.warning("Geen audiobestand opgegeven voor transcriptie")
                return jsonify({'error': 'Geen audiobestand opgegeven'}), 400
            
            if not os.path.exists(audio_file):
                logger.error(f"Audiobestand niet gevonden: {audio_file}")
                return jsonify({
                    'error': 'Audiobestand niet gevonden',
                    'details': f'Het bestand {audio_file} bestaat niet'
                }), 404
            
            # Controleer of taal ondersteund wordt
            supported = supported_languages()
            if language not in supported:
                logger.warning(f"Niet-ondersteunde taal opgegeven: {language}")
                return jsonify({
                    'error': 'Niet-ondersteunde taal',
                    'details': f'De taal {language} wordt niet ondersteund. Ondersteunde talen: {", ".join(supported.keys())}'
                }), 400
            
            logger.info(f"Start transcriptie van: {audio_file} in taal: {language}")
            text = transcribe_audio(audio_file, language)
            
            if text == "Kon geen spraak herkennen in de opname.":
                logger.warning(f"Geen spraak herkend in: {audio_file}")
                return jsonify({
                    'warning': 'Geen spraak herkend',
                    'text': text,
                    'filename': os.path.basename(audio_file).replace('.wav', '.txt')
                }), 200
            
            filename = os.path.basename(audio_file).replace('.wav', '.txt')
            file_path = save_transcription(text, filename)
            logger.info(f"Transcriptie opgeslagen als: {file_path}")
            
            return jsonify({
                'text': text,
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'language': language
            })
        except ValueError as e:
            logger.error(f"Validatiefout bij transcriptie: {str(e)}")
            return jsonify({
                'error': 'Validatiefout',
                'details': str(e)
            }), 400
        except FileNotFoundError as e:
            logger.error(f"Bestand niet gevonden: {str(e)}")
            return jsonify({
                'error': 'Bestand niet gevonden',
                'details': str(e)
            }), 404
        except Exception as e:
            logger.error(f"Fout bij transcriptie: {str(e)}")
            return jsonify({
                'error': 'Kon transcriptie niet uitvoeren',
                'details': str(e)
            }), 500
    
    @app.route('/api/languages', methods=['GET'])
    def api_languages():
        """API endpoint om ondersteunde talen op te halen."""
        try:
            languages = supported_languages()
            logger.info(f"Ondersteunde talen opgehaald: {len(languages)}")
            return jsonify({'languages': languages})
        except Exception as e:
            logger.error(f"Fout bij ophalen talen: {str(e)}")
            return jsonify({
                'error': 'Kon talen niet ophalen',
                'details': str(e)
            }), 500
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handler voor 404 fouten."""
        logger.warning(f"Pagina niet gevonden: {request.path}")
        return jsonify({'error': 'Endpoint niet gevonden'}), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Handler voor 500 fouten."""
        logger.error(f"Interne serverfout: {str(e)}")
        return jsonify({'error': 'Interne serverfout'}), 500
