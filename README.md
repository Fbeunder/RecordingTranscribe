# Record en Transcribe App

Een Python en Web applicatie om gesprekken op te nemen en om te zetten naar geschreven transcripties.

## Functionaliteiten

- Web-gebaseerde gebruikersinterface
- Selecteren van een microfoon voor opname
- Starten en stoppen van geluidsopnamen
- Automatisch opslaan in de standaard download map van de browser
- Transcriberen van opgenomen audio naar tekst
- Importeren en transcriberen van eerder opgenomen audiobestanden

## Installatie

1. Clone deze repository
```bash
git clone https://github.com/Fbeunder/RecordingTranscribe.git
cd RecordingTranscribe
```

2. Maak een virtuele Python-omgeving en activeer deze (optioneel maar aanbevolen)
```bash
python -m venv venv
source venv/bin/activate  # Voor Linux/macOS
# of
venv\Scripts\activate     # Voor Windows
```

3. Installeer de benodigde packages
```bash
pip install -r requirements.txt
```

## Gebruik

1. Start de applicatie
```bash
python app.py
```

2. Open je browser en ga naar `http://localhost:5000`

3. Volg de instructies in de webinterface om een opname te starten of een bestaand audiobestand te transcriberen

## Technische Details

Deze applicatie is gebouwd met:
- Python
- Flask voor de webserver
- PyAudio voor de audio-opname functionaliteit
- SpeechRecognition voor de transcriptie van audio naar tekst

## Projectstructuur

```
RecordingTranscribe/
├── app.py                 # Hoofdbestand om de applicatie te starten
├── requirements.txt       # Benodigde Python packages
├── README.md              # Documentatie en gebruiksinstructies
├── static/                # Statische bestanden voor de web-interface
│   ├── css/               # CSS-bestanden
│   ├── js/                # JavaScript-bestanden
│   └── img/               # Afbeeldingen
├── templates/             # HTML-templates
├── modules/
│   ├── __init__.py        # Maakt modules/ tot een Python package
│   ├── recorder.py        # Module voor audio-opname functionaliteit
│   ├── transcriber.py     # Module voor transcriptie functionaliteit
│   ├── file_handler.py    # Module voor bestandsbeheer
│   └── web_interface.py   # Module voor de web GUI
└── tests/                 # Unit tests
    ├── __init__.py        # Maakt tests/ tot een Python package
    ├── test_recorder.py   # Tests voor recorder.py
    ├── test_transcriber.py# Tests voor transcriber.py
    └── test_file_handler.py # Tests voor file_handler.py
```

## Licentie

[MIT License](LICENSE)
