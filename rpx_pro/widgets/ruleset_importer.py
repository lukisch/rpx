"""RulesetImporter + RulesetImportDialog: Regelwerk-Import-System."""

import json
import logging
from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QGroupBox, QCheckBox, QDialogButtonBox, QFileDialog, QMessageBox,
)

from rpx_pro.constants import RULESETS_DIR, logger
from rpx_pro.models.enums import DamageType, SpellEffect, SpellTarget
from rpx_pro.models.entities import (
    Race, Weapon, Armor, Spell, DiceRule,
)
from rpx_pro.models.world import World
from rpx_pro.managers.data_manager import DataManager


class RulesetImporter:
    """Importiert Regelwerk-Templates in eine Welt"""

    @staticmethod
    def list_builtin_rulesets() -> List[Dict[str, str]]:
        """Listet alle eingebauten Regelwerk-Templates"""
        rulesets = []
        if RULESETS_DIR.exists():
            for path in sorted(RULESETS_DIR.glob("*.json")):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    rulesets.append({
                        "path": str(path),
                        "id": data.get("ruleset_id", path.stem),
                        "name": data.get("ruleset_name", path.stem),
                        "description": data.get("description", ""),
                    })
                except Exception as e:
                    logger.warning(f"Regelwerk-Datei konnte nicht geladen werden: {path} -- {e}")
        return rulesets

    @staticmethod
    def load_template(path: str) -> Optional[Dict]:
        """Laedt ein Regelwerk-Template"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden des Regelwerks: {e}")
            return None

    @staticmethod
    def preview(template: Dict) -> Dict[str, int]:
        """Gibt eine Vorschau der importierbaren Elemente zurueck"""
        return {
            "races": len(template.get("races", {})),
            "professions": len(template.get("professions", [])),
            "weapons": len(template.get("weapons", {})),
            "armors": len(template.get("armors", {})),
            "spells": len(template.get("spells", {})),
            "dice_rules": len(template.get("dice_rules", {})),
        }

    @staticmethod
    def import_ruleset(world: World, template: Dict,
                       categories: Optional[set] = None) -> Dict[str, int]:
        """Importiert ein Template in eine bestehende Welt."""
        counts: Dict[str, int] = {}
        all_cats = {"races", "professions", "weapons", "armors", "spells", "dice_rules"}
        cats = categories if categories else all_cats

        if "races" in cats:
            for rid, rdata in template.get("races", {}).items():
                world.races[rid] = Race(
                    id=rid,
                    name=rdata.get("name", rid),
                    description=rdata.get("description", ""),
                    abilities=rdata.get("abilities", []),
                    strengths=rdata.get("strengths", []),
                    weaknesses=rdata.get("weaknesses", []),
                    hunger_modifier=rdata.get("hunger_modifier", 1.0),
                    thirst_modifier=rdata.get("thirst_modifier", 1.0),
                )
            counts["races"] = len(template.get("races", {}))

        if "professions" in cats:
            profs = template.get("professions", [])
            for p in profs:
                if p not in world.professions:
                    world.professions.append(p)
            counts["professions"] = len(profs)

        if "weapons" in cats:
            for wid, wdata in template.get("weapons", {}).items():
                dmg_type = wdata.get("damage_type", "physical")
                try:
                    dt = DamageType(dmg_type)
                except ValueError:
                    dt = DamageType.PHYSICAL
                world.weapons[wid] = Weapon(
                    id=wid,
                    name=wdata.get("name", wid),
                    damage_min=wdata.get("damage_min", 1),
                    damage_max=wdata.get("damage_max", 6),
                    damage_avg=wdata.get("damage_avg", 3),
                    damage_type=dt,
                    accuracy=wdata.get("accuracy", 0.8),
                    required_strength=wdata.get("required_strength", 0),
                    required_level=wdata.get("required_level", 1),
                    description=wdata.get("description", ""),
                )
            counts["weapons"] = len(template.get("weapons", {}))

        if "armors" in cats:
            for aid, adata in template.get("armors", {}).items():
                world.armors[aid] = Armor(
                    id=aid,
                    name=adata.get("name", aid),
                    protection_min=adata.get("protection_min", 1),
                    protection_max=adata.get("protection_max", 5),
                    protection_avg=adata.get("protection_avg", 3),
                    reliability=adata.get("reliability", 0.9),
                    description=adata.get("description", ""),
                )
            counts["armors"] = len(template.get("armors", {}))

        if "spells" in cats:
            for sid, sdata in template.get("spells", {}).items():
                try:
                    eff = SpellEffect(sdata.get("effect_type", "damage"))
                except ValueError:
                    eff = SpellEffect.DAMAGE
                try:
                    tgt = SpellTarget(sdata.get("target_type", "single_enemy"))
                except ValueError:
                    tgt = SpellTarget.SINGLE_ENEMY
                world.spells[sid] = Spell(
                    id=sid,
                    name=sdata.get("name", sid),
                    effect_type=eff,
                    effect_value=sdata.get("effect_value", 10),
                    target_type=tgt,
                    mana_cost=sdata.get("mana_cost", 10),
                    required_level=sdata.get("required_level", 1),
                    required_intelligence=sdata.get("required_intelligence", 0),
                    description=sdata.get("description", ""),
                )
            counts["spells"] = len(template.get("spells", {}))

        if "dice_rules" in cats:
            for drid, drdata in template.get("dice_rules", {}).items():
                ranges = {}
                for label, vals in drdata.get("ranges", {}).items():
                    ranges[label] = tuple(vals) if isinstance(vals, list) else vals
                world.dice_rules[drid] = DiceRule(
                    id=drid,
                    name=drdata.get("name", drid),
                    dice_count=drdata.get("dice_count", 1),
                    dice_sides=drdata.get("dice_sides", 20),
                    ranges=ranges,
                    description=drdata.get("description", ""),
                )
            counts["dice_rules"] = len(template.get("dice_rules", {}))

        if template.get("ruleset_name"):
            world.settings.genre = template["ruleset_name"]

        logger.info(f"Regelwerk importiert: {template.get('ruleset_name', '?')} -> {counts}")
        return counts


class RulesetImportDialog(QDialog):
    """Dialog zum Importieren von Regelwerk-Templates"""

    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.template: Optional[Dict] = None
        self.template_path: Optional[str] = None
        self.setWindowTitle("Regelwerk importieren")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        source_group = QGroupBox("Regelwerk auswaehlen")
        source_layout = QVBoxLayout(source_group)

        self.ruleset_combo = QComboBox()
        builtin = RulesetImporter.list_builtin_rulesets()
        for rs in builtin:
            self.ruleset_combo.addItem(f"{rs['name']}", rs["path"])
        self.ruleset_combo.addItem("Eigene Datei laden...", "__custom__")
        self.ruleset_combo.currentIndexChanged.connect(self._on_ruleset_changed)
        source_layout.addWidget(self.ruleset_combo)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        source_layout.addWidget(self.desc_label)
        layout.addWidget(source_group)

        self.preview_group = QGroupBox("Vorschau")
        self.preview_layout = QVBoxLayout(self.preview_group)
        self.preview_label = QLabel("Bitte Regelwerk auswaehlen")
        self.preview_layout.addWidget(self.preview_label)
        layout.addWidget(self.preview_group)

        cat_group = QGroupBox("Kategorien importieren")
        cat_layout = QVBoxLayout(cat_group)
        self.cat_checks = {}
        labels = {"races": "Voelker/Rassen", "professions": "Professionen/Klassen",
                  "weapons": "Waffen", "armors": "Ruestungen",
                  "spells": "Zauber", "dice_rules": "Wuerfelregeln"}
        for key, label in labels.items():
            cb = QCheckBox(label)
            cb.setChecked(True)
            self.cat_checks[key] = cb
            cat_layout.addWidget(cb)
        layout.addWidget(cat_group)

        target_group = QGroupBox("Ziel")
        target_layout = QVBoxLayout(target_group)
        self.target_combo = QComboBox()
        self.target_combo.addItem("Neue Welt erstellen", "__new__")
        for wid, w in self.data_manager.worlds.items():
            self.target_combo.addItem(f"{w.settings.name} ({w.settings.genre})", wid)
        target_layout.addWidget(self.target_combo)
        layout.addWidget(target_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.ruleset_combo.count() > 0:
            self._on_ruleset_changed(0)

    def _on_ruleset_changed(self, index):
        path = self.ruleset_combo.currentData()
        if path == "__custom__":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Regelwerk-Datei oeffnen", "", "JSON (*.json)")
            if not file_path:
                self.ruleset_combo.blockSignals(True)
                self.ruleset_combo.setCurrentIndex(0)
                self.ruleset_combo.blockSignals(False)
                return
            path = file_path

        self.template = RulesetImporter.load_template(path)
        self.template_path = path
        if self.template:
            self.desc_label.setText(self.template.get("description", ""))
            preview = RulesetImporter.preview(self.template)
            lines = []
            labels = {"races": "Voelker", "professions": "Professionen",
                      "weapons": "Waffen", "armors": "Ruestungen",
                      "spells": "Zauber", "dice_rules": "Wuerfelregeln"}
            for key, label in labels.items():
                count = preview.get(key, 0)
                lines.append(f"  {label}: {count}")
            self.preview_label.setText("\n".join(lines))
        else:
            self.preview_label.setText("Fehler beim Laden")

    def _on_accept(self):
        if not self.template:
            QMessageBox.warning(self, "Fehler", "Kein Regelwerk geladen!")
            return

        cats = set()
        for key, cb in self.cat_checks.items():
            if cb.isChecked():
                cats.add(key)

        if not cats:
            QMessageBox.warning(self, "Fehler", "Keine Kategorien ausgewaehlt!")
            return

        target = self.target_combo.currentData()
        if target == "__new__":
            name = self.template.get("ruleset_name", "Neue Welt")
            world = self.data_manager.create_world(name, name)
        else:
            world = self.data_manager.worlds.get(target)
            if not world:
                QMessageBox.warning(self, "Fehler", "Welt nicht gefunden!")
                return

        counts = RulesetImporter.import_ruleset(world, self.template, cats)
        self.data_manager.save_world(world)
        self.data_manager.current_world = world

        summary = "\n".join(f"  {k}: {v}" for k, v in counts.items() if v > 0)
        QMessageBox.information(self, "Import abgeschlossen",
                                f"Regelwerk '{self.template.get('ruleset_name', '?')}' importiert:\n\n{summary}")
        self.accept()
