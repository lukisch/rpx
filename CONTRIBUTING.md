# Beitragsrichtlinie / Contributing Guide

## Deutsch

Vielen Dank für Ihr Interesse, zu RPX Pro beizutragen.

### Wie Sie beitragen können

1. **Bug melden:** Erstellen Sie ein Issue mit dem Label `bug`.
2. **Feature vorschlagen:** Erstellen Sie ein Issue mit dem Label `enhancement`.
3. **Code beitragen:** Erstellen Sie einen Pull Request gegen `master`.

### Pull Requests

1. Forken Sie das Repository: https://github.com/entertain-and-more/rpx
2. Erstellen Sie einen Feature-Branch: `git checkout -b feature/mein-feature`
3. Committen Sie Ihre Änderungen: `git commit -m "Beschreibung der Änderung"`
4. Pushen Sie den Branch: `git push origin feature/mein-feature`
5. Erstellen Sie einen Pull Request.

### Lizenzierung

Dieses Projekt steht unter der MIT-Lizenz. Mit einem Pull Request bestätigen Sie, dass Sie das Recht haben, Ihre Änderungen unter der MIT-Lizenz einzureichen. Ein separates CLA-Dokument ist aktuell nicht erforderlich.

### Code-Richtlinien

- Python: PEP 8 Stil
- Encoding: UTF-8 für alle Textdateien
- Sprache: Code und Kommentare auf Deutsch oder Englisch
- Keine hardcoded lokalen Pfade, privaten Daten oder API-Keys
- Nutzerdaten bleiben in `rpx_pro_data/` und werden nicht eingecheckt

### Erste Schritte

```bash
git clone https://github.com/entertain-and-more/rpx.git
cd rpx
pip install -r requirements.txt
python RPX_Pro_1.py
```

---

## English

Thank you for your interest in contributing to RPX Pro.

### How to Contribute

1. **Report bugs:** Create an issue with the `bug` label.
2. **Suggest features:** Create an issue with the `enhancement` label.
3. **Contribute code:** Open a pull request against `master`.

### Pull Requests

1. Fork the repository: https://github.com/entertain-and-more/rpx
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Description of change"`
4. Push the branch: `git push origin feature/my-feature`
5. Open a pull request.

### Licensing

This project is licensed under the MIT License. By submitting a pull request, you confirm that you have the right to submit your changes under the MIT License. A separate CLA document is not currently required.

### Code Guidelines

- Python: PEP 8 style
- Encoding: UTF-8 for all text files
- Language: Code and comments in German or English
- No hardcoded local paths, private data, or API keys
- User data stays in `rpx_pro_data/` and must not be committed

### Getting Started

```bash
git clone https://github.com/entertain-and-more/rpx.git
cd rpx
pip install -r requirements.txt
python RPX_Pro_1.py
```
