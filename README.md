# RPX Pro - RolePlay Xtreme Professional Edition

Ein professionelles Rollenspiel-Kontrollzentrum fuer Pen & Paper Abenteuer. Offline-faehig, kostenlos, Open Source.

## Features

| Feature | Beschreibung |
|---------|-------------|
| **Welten-System** | Karten, Orte (Aussen-/Innenansicht), Nationen, Voelker, Trigger-Automatisierung |
| **Soundboard** | Multi-Backend Audio (Qt Multimedia, pygame, winsound) |
| **Lichteffekte** | Blitz, Stroboskop, Tag/Nacht-Zyklus, Farbfilter (konfigurierbar fuer Spieler-Bildschirm) |
| **Kampfsystem** | Waffen, Ruestungen, Magie, Kampftechniken, konfigurierbares Wuerfelsystem |
| **Spieler-Bildschirm** | Separater Monitor fuer Spieler mit Bildern, Effekten und Statusanzeige |
| **Regelwerk-Import** | D&D 5e, DSA 5, Generisches Fantasy (oder eigene JSON-Templates) |
| **KI-Integration** | Promptgenerator mit 7 spezialisierten KI-Rollen |
| **Session-Manager** | Missionen (abschliessen/scheitern), Gruppen, Rundensteuerung |
| **Charaktere** | Attribute, Inventar, Bearbeitung, Avatar, Hunger/Durst-Simulation |
| **Simulation** | Hunger/Durst-Timer, Zeitfortschritt, Naturkatastrophen |

## Installation

```bash
# Abhaengigkeiten installieren
pip install -r requirements.txt

# Starten
python RPX_Pro_1.py
```

Oder unter Windows: `START.bat` doppelklicken.

### Voraussetzungen

- Python 3.10+
- PySide6 (Qt6) - beinhaltet Qt Multimedia fuer Audio
- pygame (optional, Audio-Fallback)

## Schnellstart

1. **Welt erstellen**: Welt-Tab > "Neue Welt" > Name eingeben
2. **Karte hinterlegen**: Welt-Tab > "Karte laden..." > Bilddatei auswaehlen
3. **Orte anlegen**: Welt-Tab > "Ort hinzufuegen" > mit "Bearbeiten" Bilder/Sound zuweisen
4. **Session starten**: Datei > Neue Session > Welt auswaehlen
5. **Charaktere erstellen**: Charaktere-Tab > "Charakter erstellen" > mit "Bearbeiten" Details setzen
6. **Spiel starten**: Toolbar > "Spiel starten" > KI-Prompt wird in die Zwischenablage kopiert

## Tab-Uebersicht

### Chat (Tab 1)
- Nachrichten mit verschiedenen Rollen (Spieler, GM, KI-Rollen, Erzaehler)
- Farbcodierung nach Rolle
- System-Events werden automatisch geloggt (Wuerfelergebnisse, Ortswechsel, etc.)

### Ortsansicht (Tab 2)
- Klick auf einen Ort im Welt-Tab oeffnet automatisch die Ortsansicht
- Aussen-/Innenansicht mit Uebergangseffekt (Blackout beim Betreten)
- Farbfilter pro Ort konfigurierbar
- Trigger-System: Sounds/Licht/Chatnachrichten beim Betreten/Verlassen

### Welt (Tab 3)
- Welten erstellen, bearbeiten, speichern
- **Weltkarte** hinterlegen (wird auf dem Spieler-Bildschirm angezeigt)
- Orte im Baum verwalten (hinzufuegen, bearbeiten mit Dialog)
- Klick auf Ort = Ortsansicht oeffnen

### Charaktere (Tab 4)
- Tabelle aller Charaktere mit Kerndaten
- **Bearbeiten**: Voller Dialog fuer Name, Spieler, Rasse, Beruf, Level, Leben, Mana, NPC-Status, Biografie
- **Loeschen**: Mit Bestaetigung
- Linkes Panel zeigt aktive Spielercharaktere mit Avatar und Statusbalken

### Kampf (Tab 5)
- Wuerfelsystem (1-10 Wuerfel, W4 bis W100)
- Ergebnisse im Chat protokolliert
- Waffen- und Zauberlisten (werden beim Weltwechsel/Session-Laden aktualisiert)

### Missionen (Tab 6)
- Aktive und abgeschlossene Missionen
- Missionen **abschliessen** oder als **gescheitert** markieren
- Status-Aenderungen werden im Chat geloggt

### Immersion (Tab 7)
- **Soundboard**: Sounds per Drag&Drop oder Dialog hinzufuegen
- **Lichteffekte**: Blitz, Stroboskop, Tag/Nacht, Farbfilter
- **Hintergrundmusik**: Dateien aus media/music/ abspielen
- Alle Effekte werden (konfigurierbar) auf den Spieler-Bildschirm gespiegelt

### KI-Prompts (Tab 8)
- 7 KI-Rollen: Storyteller, Plottwist, Spielleiter, Gegner, NPCs, Landschaft, Fauna/Flora
- Spielstart-Prompt mit allen Weltinfos generieren
- Update-Prompt mit letztem Spielverlauf
- In Zwischenablage kopieren

### Einstellungen (Tab 9)
- **Session**: Rundenmodus, Aktionen/Runde, Spielleiter (Mensch/KI)
- **Welt**: Zeitverhaeltnis, Stunden/Tag, Hunger/Durst-Simulation, Naturkatastrophen
- **Effekte**: Lichteffekte/Tag-Nacht/Farbfilter einzeln fuer Spieler-Bildschirm an/ausschalten
- **Spieler-Bildschirm**: Oeffnen/Schliessen, Monitor-Auswahl, Vollbild, Schwarzbild, Karte zeigen

## Simulation

### Hunger/Durst
- Wenn aktiviert, steigen Hunger/Durst aller Charaktere proportional zur Spielzeit
- Warnungen im Chat bei 50% und 75%
- Rate pro Spielstunde konfigurierbar (`hunger_rate`, `thirst_rate` im Charakter)
- Rassen-Modifikatoren moeglich (`hunger_modifier`, `thirst_modifier`)

### Naturkatastrophen
- Zufallsereignisse basierend auf `disaster_probability` (Standard: 0.5%)
- Ereignisse: Erdbeben, Ueberschwemmung, Vulkanausbruch, Tornado, Duerren, etc.
- Visueller Stroboskop-Effekt + Chat-Nachricht
- Rate skaliert mit dem Zeitverhaeltnis

### Zeitfortschritt
- Spielzeit laeuft proportional zur Echtzeit (Verhaeltnis konfigurierbar)
- Tageswechsel-Benachrichtigungen im Chat
- Tageszeit wird automatisch auf dem Spieler-Bildschirm aktualisiert

## Spieler-Bildschirm (2. Monitor)

Der GM kann einen separaten Bildschirm fuer Spieler oeffnen (Einstellungen-Tab):

- Zeigt Ortsbilder (Aussen-/Innenansicht), Karten oder eigene Bilder
- Lichteffekte koennen **einzeln** an/ausgeschaltet werden:
  - Blitz/Stroboskop-Spiegelung
  - Tag/Nacht-Spiegelung
  - Farbfilter-Spiegelung
- Monitor-Auswahl und Vollbild-Modus
- Schwarzbild-Funktion fuer Pausen
- Wetter- und Zeitanzeige in der Statusleiste

## Regelwerk-Import

RPX bringt drei Regelwerk-Templates mit:

- **D&D 5e (SRD)** - 9 Rassen, 19 Waffen, 12 Ruestungen, 14 Zauber
- **DSA 5 (Abstrahiert)** - 12 Voelker, 15 Waffen, 7 Ruestungen, 12 Zauber
- **Generisches Fantasy** - 5 Rassen, 10 Waffen, 5 Ruestungen, 10 Zauber

Eigene Regelwerke koennen als JSON-Datei importiert werden (`Datei > Regelwerk importieren`).

## Datenstruktur

```
rpx_pro_data/
  config.json          # Globale Einstellungen
  worlds/              # Welt-JSONs (Orte, Waffen, Rassen, etc.)
  sessions/            # Session-JSONs (Charaktere, Missionen, Chat)
  media/
    sounds/            # Sound-Effekte (.mp3, .wav, .ogg)
    music/             # Hintergrundmusik
    images/            # Orts-/Charakter-Bilder
    maps/              # Weltkarten
  backups/             # Auto-Backups geloeschter Welten/Sessions
```

## Tastenkuerzel

| Kuerzel | Aktion |
|---------|--------|
| Ctrl+N | Neue Session |
| Ctrl+O | Session laden |
| Ctrl+S | Session speichern |

## Markt-Vergleich

| Feature | RPX | Roll20 | Foundry VTT | Fantasy Grounds |
|---------|:---:|:------:|:-----------:|:---------------:|
| Offline-faehig | x | - | x | x |
| Lichteffekte | x | - | ~ | - |
| KI-Integration | x | - | ~ | - |
| Hunger-Simulation | x | - | - | - |
| Naturkatastrophen | x | - | - | - |
| 2. Monitor | x | - | ~ | ~ |
| Kostenlos | x | ~ | - | - |
| Open Source | x | - | - | - |

## Lizenz

AGPL-3.0 - siehe [LICENSE](LICENSE).

RPX ist freie Software: Du kannst es unter den Bedingungen der GNU Affero General Public License (Version 3 oder spaeter) weitergeben und/oder modifizieren. Fuer kommerzielle Nutzung ohne Copyleft-Pflicht kontaktiere den Autor.

Die Regelwerk-Templates enthalten nur generische Spielmechaniken. D&D-Inhalte basieren auf dem SRD 5.1 (OGL). DSA-Inhalte sind abstrahiert und enthalten keine geschuetzten Texte.
