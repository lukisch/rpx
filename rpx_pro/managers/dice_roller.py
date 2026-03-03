"""DiceRoller: Wuerfelsystem mit konfigurierbaren Regeln."""

import random
import time
from typing import Dict, List, Any

from rpx_pro.models.entities import DiceRule


class DiceRoller:
    """Wuerfelsystem mit konfigurierbaren Regeln"""

    def __init__(self):
        self.rules: Dict[str, DiceRule] = {}
        self.history: List[Dict[str, Any]] = []

    def add_rule(self, rule: DiceRule):
        """Fuegt eine Wuerfelregel hinzu"""
        self.rules[rule.id] = rule

    def roll(self, rule_id: str = None, dice_count: int = 1, dice_sides: int = 20) -> Dict[str, Any]:
        """Wuerfelt nach Regel oder frei"""
        dice_count = max(1, dice_count)
        dice_sides = max(1, dice_sides)
        rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]
        total = sum(rolls)

        result = {
            "rolls": rolls,
            "total": total,
            "dice": f"{dice_count}W{dice_sides}",
            "timestamp": time.time(),
            "outcome": None
        }

        if rule_id and rule_id in self.rules:
            rule = self.rules[rule_id]
            for outcome_name, (min_val, max_val) in rule.ranges.items():
                if min_val <= total <= max_val:
                    result["outcome"] = outcome_name
                    break

        self.history.append(result)
        return result

    def get_last_rolls(self, count: int = 10) -> List[Dict[str, Any]]:
        """Gibt die letzten Wuerfe zurueck"""
        return self.history[-count:]
