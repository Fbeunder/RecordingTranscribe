#!/usr/bin/env python3
"""
File handler module voor de Record en Transcribe applicatie.

Deze module verzorgt het bestandsbeheer voor opnames en transcripties.
Het biedt functionaliteit voor het bepalen van de download map,
het opslaan van bestanden en het laden van bestanden.
"""

import os
from typing import Union


def get_download_folder() -> str:
    """
    Bepaalt de standaard download-map van de browser.
    
    Returns:
        str: Pad naar de download-map
    """
    # TODO: Implementeer het bepalen van de download map
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
    # TODO: Implementeer het opslaan van een bestand
    if folder is None:
        folder = get_download_folder()
    
    # Placeholder voor de implementatie
    return os.path.join(folder, filename)


def load_file(filepath: str) -> Union[bytes, str]:
    """
    Laadt een bestand van schijf.
    
    Args:
        filepath (str): Pad naar het bestand
        
    Returns:
        bytes of str: Inhoud van het bestand
    """
    # TODO: Implementeer het laden van een bestand
    # Placeholder voor de implementatie
    return b""  # of "" voor tekstbestanden
