
INFO - Terminal Befehle stehen in <> - Nur den Inhalt kopieren!
INFO - https://code.visualstudio.com Visual Studio Code 

# INFO ! - Du kannst den Ordner nach C:/ verschieben, dadurch musst Du keine Pfade ändern.

# 1 - Python Version prüfen
- Terminal in Visual Studio Code öffnen (STRG + UMSCHALTEN + ö) oder Leiste oben -> Terminal/neues Terminal
- <python --version>
- es erscheint die installierte Python-Version
- wir benötigen eine Version zwischen version 3.7 und 3.9.7

# 2 - installieren der virtual Environment
- <python -m venv C:\NEWTON_EmotionVersionAlpha\.venv> Der Ordner \.venv wird dabei erstellt.
- Nun aktivieren wir die Entwicklungsumgebung mit <.\.venv\Scripts\activate>
- In der Datei "requirements.txt" sind alle benötigten Python Module aufgelistet. Diese müssen nun installiert werden.
- <pip install -r requirements.txt>

# 3 - Dateipfad zum Ordner FFmpeg setzen (obsolet wenn der Ordner unter C:/ liegt)
- In der Datei "FE_Setup.json" sind verschiedene Programmeinstellungen verfügbar.
- Hier setzen wir den Pfad zum Ordner "FFmpeg". 
- Im EXPLORER kannst Du den absoluten Pfad kopieren (Rechtsklick \ Pfad kopieren)

# 4 - Dateipfad zu den Audio-Dateien setzen (obsolet wenn der Ordner unter C:/ liegt)
- Momentan ist die Stapelverarbeitung aktiviert (ALLE Audio-Dateien im Ordner werden verarbeitet)
- In der Datei "FeatureExtractor.py" Codezeile 318 muss der Pfad geändert werden
- src = "C:\\NEWTON_EmotionVersionAlpha\\_src"
- Wie in Schritt 3 kannst du im EXPLORER den absoluten Pfad des Ordners "_src" kopieren und in die Codezeile einfügen.
- hierbei ist es wichtig, dass der Backslash doppelt geschrieben wird! 

# 5 - Starten der Funktion
- Starte das Script über die Datei "FeatureExtractor.py"
- Entweder über den Play-Button in Visual Studio Code oder über den Konsolen-Befehl: <python FeatureExtractor.py>
- Im _src Ordner in der Datei _src.txt findest Du nun die Auswertung



