# RPX - RolePlay Xtreme

Ein professionelles Rollenspiel-Kontrollzentrum fuer Pen & Paper Abenteuer. Offline-faehig, kostenlos, Open Source.

## Features

| Feature | Beschreibung |
|---------|-------------|
| **Welten-System** | Karten, Orte, Nationen, Voelker, Trigger-Automatisierung |
| **Soundboard** | Multi-Backend Audio (Qt, pygame, winsound) |
| **Lichteffekte** | Blitz, Stroboskop, Tag/Nacht-Zyklus, Farbfilter |
| **Kampfsystem** | Waffen, Ruestungen, Magie, Kampftechniken |
| **Spieler-Bildschirm** | Separater Monitor fuer Spieler mit Bildern und Effekten |
| **Regelwerk-Import** | D&D 5e, DSA 5, Generisches Fantasy (oder eigene Templates) |
| **KI-Integration** | Promptgenerator mit 7 spezialisierten KI-Rollen |
| **Session-Manager** | Missionen, Gruppen, Rundensteuerung |
| **Charaktere** | Attribute, Inventar, Hunger/Durst-Simulation |
| **Wuerfelsystem** | Konfigurierbar (NdX), Chat-Integration |

## Installation

```bash
# Repository klonen
git clone https://github.com/lukisch/rpx.git
cd rpx

# Abhaengigkeiten installieren
pip install -r requirements.txt

# Starten
python RPX_Pro_1.py
```

Oder unter Windows: `START.bat` doppelklicken.

### Voraussetzungen

- Python 3.10+
- PySide6 (Qt6)
- pygame (optional, Audio-Fallback)

## Regelwerk-Import

RPX bringt drei Regelwerk-Templates mit:

- **D&D 5e (SRD)** - 9 Rassen, 19 Waffen, 12 Ruestungen, 14 Zauber
- **DSA 5 (Abstrahiert)** - 12 Voelker, 15 Waffen, 7 Ruestungen, 12 Zauber
- **Generisches Fantasy** - 5 Rassen, 10 Waffen, 5 Ruestungen, 10 Zauber

Eigene Regelwerke koennen als JSON-Datei importiert werden (`Datei > Regelwerk importieren`).

## Spieler-Bildschirm

Der GM kann einen separaten Bildschirm fuer Spieler oeffnen (Einstellungen-Tab):

- Zeigt Ortsbilder, Karten oder eigene Bilder
- Lichteffekte werden automatisch gespiegelt
- Monitor-Auswahl und Vollbild-Modus
- Schwarzbild-Funktion fuer Pausen

## Markt-Vergleich

| Feature | RPX | Roll20 | Foundry VTT | Fantasy Grounds |
|---------|:---:|:------:|:-----------:|:---------------:|
| Offline-faehig | x | - | x | x |
| Lichteffekte | x | - | ~ | - |
| KI-Integration | x | - | ~ | - |
| Kostenlos | x | ~ | - | - |
| Open Source | x | - | - | - |

## Lizenz

MIT License - siehe [LICENSE](LICENSE).

Die Regelwerk-Templates enthalten nur generische Spielmechaniken. D&D-Inhalte basieren auf dem SRD 5.1 (OGL). DSA-Inhalte sind abstrahiert und enthalten keine geschuetzten Texte.
