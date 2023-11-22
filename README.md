# Kleinanzeigen Telegram Bot

![Banner generated with Dall-E](banner.png)

## Überblick
Dieser Telegram Bot hält Ausschau auf der Kleinanzeigen-Webseite nach neuen Angeboten, die zu benutzerdefinierten Suchbegriffen und Zeitintervallen passen. Der Bot nutzt die Telegram API, um Benutzer über neue Angebote zu informieren.

## Funktionsweise
- **Überwachung**: Der Bot durchsucht ständig Kleinanzeigen nach bestimmten Suchbegriffen.
- **Benachrichtigungen**: Benutzer erhalten automatische Updates in Telegram, wenn neue Angebote gefunden werden.
- **Anpassbarkeit**: Benutzer können Suchbegriffe und Zeitintervalle nach ihren Wünschen festlegen.

## Einrichtung
1. **Voraussetzungen**:
   - Python 3.6 oder neuer
   - Erforderliche Bibliotheken: `telegram`, `beautifulsoup4`, `multiprocessing`, `threading`, `asyncio`.

2. **Bot Token**:
   - Erstelle einen neuen Bot über [BotFather](https://t.me/botfather) in Telegram und kopiere das Bot-Token.

3. **Konfiguration**:
   - Ersetze `BOT_TOKEN` in der Hauptdatei durch dein persönliches Bot-Token.

4. **Abhängigkeiten installieren**:
   - Führe `pip install -r requirements.txt` aus, um die benötigten Bibliotheken zu installieren.

## Verwendung
- **Bot starten**: Führe `python telegram_bot.py` aus.
- **Arbeiter starten**: Sende `/startworker` im Chat, um die Überwachung zu beginnen.
- **Suchbegriff festlegen**: Folge den Anweisungen im Chat, um Suchbegriffe und Intervalle festzulegen.
- **Arbeiter stoppen**: Sende `/stopworker`, um die Überwachung zu beenden.
- **Arbeiter auflisten**: Sende `/listworker`, um aktive Arbeiter anzuzeigen.

## Erweiterte Funktionen
- **Fehlerbehandlung**: Der Bot verfügt über ein zuverlässiges Fehlerbehandlungssystem.
- **Protokollierung**: Umfangreiche Protokollierungsfunktionen unterstützen bei der Fehlerbehebung.

## Lizenz
Dieses Projekt steht unter der MIT-Lizenz. Es ist für private und kommerzielle Nutzung frei verfügbar.

## Mitwirken
Verbesserungen und Vorschläge sind jederzeit willkommen. Bitte erstelle Pull-Anfragen oder meldet Probleme im GitHub-Repository.

## Haftungsausschluss
Dieser Bot hat keine Verbindung zur offiziellen Kleinanzeigen-Webseite und dient ausschließlich zu Bildungszwecken.