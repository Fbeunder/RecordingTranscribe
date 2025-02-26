#!/usr/bin/env python3
"""
Record en Transcribe App - Hoofdapplicatie

Dit is het hoofdbestand van de applicatie dat de Flask webserver start
en alle modules initialiseert.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request
from modules.web_interface import init_app

def configure_logging(app):
    """
    Configureert logging voor de applicatie.
    
    Args:
        app: Flask applicatie-instantie
    """
    # Zorg ervoor dat de logs map bestaat
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configureer file handler voor logs
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Configureer console handler voor logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.INFO)
    
    # Voeg handlers toe aan de app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    # Configureer root logger voor andere modules
    logging.basicConfig(
        handlers=[file_handler, console_handler],
        level=logging.INFO
    )
    
    app.logger.info('Record en Transcribe App gestart')

def create_app():
    """
    Creëert en configureert de Flask applicatie.
    
    Returns:
        Flask: Flask applicatie-instantie
    """
    app = Flask(__name__)
    
    # Configuratie van de app
    app.config['SECRET_KEY'] = 'dev-key-should-be-changed-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Configureer logging
    configure_logging(app)
    
    # Log verzoeken
    @app.before_request
    def log_request_info():
        app.logger.info(f'Request: {request.method} {request.path} {request.remote_addr}')
    
    # Registreer de web interface module
    init_app(app)
    
    return app

def main():
    """
    Start de Flask applicatie.
    """
    app = create_app()
    app.run(debug=True)

if __name__ == '__main__':
    main()
