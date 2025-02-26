#!/usr/bin/env python3
"""
File handler module voor de Record en Transcribe applicatie.

Deze module verzorgt het bestandsbeheer voor opnames en transcripties.
Het biedt functionaliteit voor het bepalen van de download map,
het opslaan van bestanden en het laden van bestanden.
"""

import os
import time
from typing import Union


def get_download_folder() -> str:
    """
    Bepaalt de standaard download-map van de browser.
    
    Returns:
        str: Pad naar de download-map
    """
    # In een webapplicatie wordt dit meestal geregeld door de browser
    # en niet door de server. Voor nu gebruiken we een relatief pad.
    download_folder = os.path.join(os.getcwd(), "downloads")
    
    # Maak de map aan als deze nog niet bestaat
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    return download_folder


def save_file(data: Union[bytes, str], filename: str, folder: str = None) -> str:
    """
    Slaat data op als een bestand.
    
    Args:
        data (bytes of str): De data die moet worden opgeslagen
        filename (str): Naam van het bestand
        folder (str, optioneel): Map waarin het bestand moet worden opgeslagen
        
    Returns:
        str: Volledig pad naar het opgeslagen bestand
    """
    if folder is None:
        folder = get_download_folder()
    
    # Zorg ervoor dat de map bestaat
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Voeg tijdstempel toe aan bestandsnaam om overschrijven te voorkomen
    name, ext = os.path.splitext(filename)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique_filename = f"{name}_{timestamp}{ext}"
    
    filepath = os.path.join(folder, unique_filename)
    
    # Sla het bestand op
    mode = 'wb' if isinstance(data, bytes) else 'w'
    with open(filepath, mode) as f:
        f.write(data)
    
    return filepath


def load_file(filepath: str) -> Union[bytes, str]:
    """
    Laadt een bestand van schijf.
    
    Args:
        filepath (str): Pad naar het bestand
        
    Returns:
        bytes of str: Inhoud van het bestand
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Bestand niet gevonden: {filepath}")
    
    # Detecteer of het een tekstbestand of binair bestand is op basis van extensie
    ext = os.path.splitext(filepath)[1].lower()
    text_extensions = ['.txt', '.json', '.csv', '.md', '.html', '.xml']
    
    if ext in text_extensions:
        # Tekstbestand
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        # Binair bestand
        with open(filepath, 'rb') as f:
            return f.read()
