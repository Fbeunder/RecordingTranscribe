#!/usr/bin/env python3
"""
Record en Transcribe App - Hoofdapplicatie

Dit is het hoofdbestand van de applicatie dat de Flask webserver start
en alle modules initialiseert.
"""

from flask import Flask, render_template
from modules.web_interface import init_app

def create_app():
    """
    Creëert en configureert de Flask applicatie.
    
    Returns:
        Flask: Flask applicatie-instantie
    """
    app = Flask(__name__)
    
    # Configuratie van de app
    app.config['SECRET_KEY'] = 'dev-key-should-be-changed-in-production'
    
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
