# RPX Pro - RolePlay Xtreme Professional Edition

Ein professionelles Rollenspiel-Kontrollzentrum fuer Pen & Paper Abenteuer. Offline-faehig, kostenlos, Open Source.

## Features

| Feature | Beschreibung |
|---------|-------------|
| **Welten-System** | Multi-Map-Karten, Orte (Aussen-/Innenansicht), Nationen, Voelker, Trigger-Automatisierung |
| **Soundboard** | Multi-Backend Audio (Qt Multimedia, pygame, winsound) |
| **Lichteffekte** | Blitz, Stroboskop, Tag/Nacht-Zyklus, Farbfilter (konfigurierbar fuer Spieler-Bildschirm) |
| **Kampfsystem** | Waffen, Ruestungen, Magie, Kampftechniken, konfigurierbares Wuerfelsystem |
| **Spieler-Bildschirm** | Separater Monitor mit dynamischen Ansichten (Kacheln, Rotation, Bilder) |
| **Regelwerk-Import** | D&D 5e, DSA 5, Generisches Fantasy (oder eigene JSON-Templates) |
| **KI-Integration** | Promptgenerator mit 7 spezialisierten KI-Rollen |
| **CLI/API** | JSON-RPC CLI fuer LLM-Steuerung via stdin/stdout |
| **Session-Manager** | Missionen, Gruppen, Rundensteuerung |
| **Charaktere** | Attribute, Inventar-Dialog, Gold, Avatar, Hunger/Durst-Simulation |
| **Simulation** | Hunger/Durst-Timer, Zeitfortschritt, Naturkatastrophen |

## Installation

```bash
# Abhaengigkeiten installieren
pip install -r requirements.txt

# Starten
python RPX_Pro_1.py
# oder direkt:
python -m rpx_pro.app
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

## Architektur

RPX Pro ist modular aufgebaut als Python-Package (`rpx_pro/`):

```
rpx_pro/
  app.py                 # Entry Point
  main_window.py         # Schlanker Orchestrator (~1200 Zeilen)
  constants.py           # Konfiguration, Pfade, Logging
  api.py                 # Programmatische Python-API (JSON-serialisierbar)
  cli.py                 # JSON-RPC CLI fuer LLM-Steuerung
  models/                # Datenmodelle (Dataclasses)
    enums.py             # MessageRole, PlayerScreenMode, DamageType, ...
    entities.py          # Character, Weapon, Armor, Spell, Item, ...
    world.py             # World, Location, WorldSettings
    session.py           # Session, ChatMessage, Mission
  managers/              # Geschaeftslogik
    data_manager.py      # Persistenz (JSON-Dateien)
    audio_manager.py     # Multi-Backend Audio
    light_manager.py     # Lichteffekte (Overlay-basiert)
    prompt_generator.py  # KI-Prompt-Erzeugung
    dice_roller.py       # Wuerfelsystem
  widgets/               # Wiederverwendbare UI-Komponenten
    chat.py              # Chat-Widget mit Rollenauswahl
    soundboard.py        # Drag&Drop Soundboard
    player_screen.py     # Spieler-Bildschirm (2. Monitor)
    map_widget.py        # Interaktive Karte mit Zeichenwerkzeugen
    location_view.py     # Ortsansicht (Aussen/Innen)
    inventory_dialog.py  # Charakter-Inventar-Dialog
    prompt_widget.py     # KI-Prompt-Generator Widget
    ruleset_importer.py  # Regelwerk-Import
  tabs/                  # Eigenstaendige Tab-Klassen
    views_tab.py         # Ansichten (Ort, Inventar, Ambiente, PlayerScreen)
    world_tab.py         # Weltverwaltung + Multi-Map
    characters_tab.py    # Charaktere + Inventar-Button
    combat_tab.py        # Kampf + Wuerfel
    missions_tab.py      # Missionen
    inventory_tab.py     # Welt-Item-Bibliothek
    immersion_tab.py     # Soundboard
    settings_tab.py      # Session-/Welt-Einstellungen
```

**Design-Prinzipien:**
- Tabs kommunizieren ausschliesslich ueber Qt Signals (kein `self.window()`)
- Manager werden per Dependency Injection uebergeben
- MainWindow ist reiner Orchestrator (verbindet Signals, routet Events)
- Models sind reine Dataclasses mit `to_dict()`/`from_dict()` Serialisierung

## Tab-Uebersicht

### Chat (Tab 1)
- Nachrichten mit verschiedenen Rollen (Spieler, GM, KI-Rollen, Erzaehler)
- Farbcodierung nach Rolle
- Chat-Befehle: `/roll`, `/heal`, `/damage`, `/check`, `/give`
- System-Events werden automatisch geloggt

### Ansichten (Tab 2)
Vier Sub-Tabs in einem:

- **Ortsansicht**: Aussen-/Innenansicht mit Blackout-Uebergang, Farbfilter, Trigger
- **Inventaransicht**: Charakter-Dropdown, Inventar-Tabelle (Name, Anzahl, Gewicht, Wert), Gold
- **Ambiente**: Lichteffekte (Blitz, Stroboskop, Tag/Nacht, Farbfilter) + Hintergrundmusik (Playlist, Lautstaerke)
- **Spieler-Bildschirm**: Monitor-Auswahl, Vollbild, Anzeigemodus, Ansichten-Checkboxen, Effekt-Spiegelung

### Welt (Tab 3)
- Welten erstellen, bearbeiten, speichern
- **Multi-Map-System**: Mehrere Karten pro Welt (Weltkarte, Dungeons, Staedte)
- Interaktive Karte mit Zeichenwerkzeugen
- Orte im Baum verwalten mit Bearbeiten-Dialog

### Charaktere (Tab 4)
- Tabelle aller Charaktere mit Kerndaten
- **Inventar-Button** pro Zeile -- oeffnet den Inventar-Dialog mit Gold, Gewicht, Items
- Bearbeiten-Dialog: Name, Rasse, Beruf, Level, HP, Mana, Skills, NPC-Status, Bild, Biografie
- Schnelle HP/Mana-Steuerung (Schaden, Heilen, Mana)

### Kampf (Tab 5)
- Wuerfelsystem (1-10 Wuerfel, W4 bis W100)
- Angriffsmechanik mit Treffsicherheit, Kritischen Treffern, Ruestung
- Waffen- und Zauberlisten

### Missionen (Tab 6)
- Aktive und abgeschlossene Missionen
- Abschliessen oder als gescheitert markieren
- Status-Aenderungen im Chat geloggt

### Inventar (Tab 7)
- Welt-Item-Bibliothek (Name, Klasse, Gewicht, Wert, Boni)
- Items an Orten mit Fundwahrscheinlichkeit
- NPCs an Orten mit Begegnungswahrscheinlichkeit

### Soundboard (Tab 8)
- Sound-Effekte per Drag&Drop oder Dialog hinzufuegen
- Play/Stop pro Sound

### KI-Prompts (Tab 9)
- 7 KI-Rollen: Storyteller, Plottwist, Spielleiter, Gegner, NPCs, Landschaft, Fauna/Flora
- Spielstart-Prompt und Update-Prompt generieren
- In Zwischenablage kopieren

### Einstellungen (Tab 10)
- Session: Rundenmodus, Aktionen/Runde, Spielleiter (Mensch/KI)
- Welt: Zeitverhaeltnis, Stunden/Tag, Hunger/Durst-Simulation, Naturkatastrophen

## Spieler-Bildschirm (2. Monitor)

Der GM kann einen separaten Bildschirm fuer Spieler oeffnen (Ansichten > Spieler-Bildschirm):

- **4 Anzeigemodi**: Bild, Karte, Rotation, Kacheln
- **Dynamische Ansichten**: Per Checkbox waehlbar welche Kacheln aktiv sind
  - Charaktere (Helden-Uebersicht mit HP/Mana-Balken)
  - Missionen (aktive Quests)
  - Karte (Weltkarte mit Markierungen)
  - Chat (Spielverlauf)
  - Rundensteuerung (Runde/Zugreihenfolge)
  - Ortsansicht (aktueller Ort)
  - Inventar (Charakter-Inventar)
- **Rotation**: Nur aktivierte Ansichten werden durchrotiert
- **Event-Overlay**: Ankuendigungen bei Schaden, Heilung, Tod, Missionen, Runden
- **Effekt-Spiegelung**: Blitz, Tag/Nacht, Farbfilter einzeln steuerbar
- Monitor-Auswahl, Vollbild, Schwarzbild

## CLI / API fuer LLM-Integration

RPX Pro bietet eine programmatische API und ein CLI-Interface fuer KI-Steuerung:

```bash
# Mit CLI starten
python -m rpx_pro.app --cli
```

**JSON-RPC Protokoll** via stdin/stdout:

```json
{"id": 1, "method": "roll_dice", "params": {"count": 2, "sides": 20}}
{"id": 1, "result": {"dice": "2W20", "rolls": [14, 7], "total": 21}}
```

**Verfuegbare Methoden:**
`create_world`, `list_worlds`, `load_world`, `create_session`, `list_sessions`, `load_session`,
`create_character`, `get_character`, `heal_character`, `damage_character`, `get_inventory`, `give_item`,
`send_chat_message`, `get_chat_history`, `roll_dice`, `create_mission`, `complete_mission`,
`generate_start_prompt`, `generate_context_update`

## Simulation

### Hunger/Durst
- Steigen proportional zur Spielzeit, Warnungen bei 50% und 75%
- Rate pro Spielstunde konfigurierbar, Rassen-Modifikatoren moeglich

### Naturkatastrophen
- Zufallsereignisse: Erdbeben, Ueberschwemmung, Vulkanausbruch, Tornado, etc.
- Visueller Stroboskop-Effekt + Chat-Nachricht

### Zeitfortschritt
- Spielzeit laeuft proportional zur Echtzeit (Verhaeltnis konfigurierbar)
- Tageswechsel-Benachrichtigungen, Tageszeit auf Spieler-Bildschirm

## Regelwerk-Import

Drei mitgelieferte Templates:

- **D&D 5e (SRD)** - 9 Rassen, 19 Waffen, 12 Ruestungen, 14 Zauber
- **DSA 5 (Abstrahiert)** - 12 Voelker, 15 Waffen, 7 Ruestungen, 12 Zauber
- **Generisches Fantasy** - 5 Rassen, 10 Waffen, 5 Ruestungen, 10 Zauber

Eigene Regelwerke als JSON importierbar (`Datei > Regelwerk importieren`).

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
  backups/             # Auto-Backups
```

## Tastenkuerzel

| Kuerzel | Aktion |
|---------|--------|
| Ctrl+N | Neue Session |
| Ctrl+O | Session laden |
| Ctrl+S | Session speichern |

## Markt-Vergleich

| Feature | RPX Pro | Roll20 | Foundry VTT | Fantasy Grounds |
|---------|:-------:|:------:|:-----------:|:---------------:|
| Offline-faehig | x | - | x | x |
| Lichteffekte | x | - | ~ | - |
| KI-Integration | x | - | ~ | - |
| LLM-API/CLI | x | - | - | - |
| Hunger-Simulation | x | - | - | - |
| Naturkatastrophen | x | - | - | - |
| 2. Monitor (dynamisch) | x | - | ~ | ~ |
| Modular/Erweiterbar | x | - | x | - |
| Kostenlos | x | ~ | - | - |
| Open Source | x | - | - | - |

## Lizenz

MIT License - siehe [LICENSE](LICENSE).

RPX Pro ist freie Software unter der MIT-Lizenz. Du kannst es frei verwenden, modifizieren und weitergeben, auch fuer kommerzielle Projekte.

Die Regelwerk-Templates enthalten nur generische Spielmechaniken. D&D-Inhalte basieren auf dem SRD 5.1 (OGL). DSA-Inhalte sind abstrahiert und enthalten keine geschuetzten Texte.

---

## English

A professional role-playing game control center with world systems, soundboard, and AI integration.

### Features

- World/campaign management
- Character sheets
- Integrated soundboard
- AI-powered storytelling
- Map viewer

### Installation

```bash
git clone https://github.com/lukisch/REL_RPG.git
cd REL_RPG
pip install -r requirements.txt
python "RPX_Pro_1.py"
```

### License

See [LICENSE](LICENSE) for details.
