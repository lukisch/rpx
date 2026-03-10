"""Welt-Datenmodelle: Location, WorldSettings, World."""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple

from rpx_pro.constants import generate_short_id, _filter_dataclass_fields
from rpx_pro.models.entities import (
    Trigger, Weapon, Armor, CombatTechnique, Spell, Item, Vehicle,
    RoadType, Nation, Race, DiceRule, GameMap,
)


@dataclass
class Location:
    """Ort in der Spielwelt mit Aussen-/Innenansicht"""
    id: str
    name: str
    description: str = ""
    parent_id: Optional[str] = None
    # Bilder
    exterior_image: Optional[str] = None
    interior_image: Optional[str] = None
    map_position: Tuple[int, int] = (0, 0)
    # Audio
    ambient_sound: Optional[str] = None
    ambient_volume: float = 0.5
    entry_sound: Optional[str] = None
    exit_sound: Optional[str] = None
    background_music: Optional[str] = None
    # Eigenschaften
    has_interior: bool = False
    visited: bool = False
    first_visit: bool = True
    # Trigger
    triggers: List[Trigger] = field(default_factory=list)
    # Farbfilter
    color_filter: Optional[str] = None
    color_filter_opacity: float = 0.3
    # Ort-Typ (fuer farbige Kartenmarker)
    location_type: str = "city"
    # Items an diesem Ort
    items: List[str] = field(default_factory=list)
    # Versteckte NPCs an diesem Ort
    hidden_npcs: Dict[str, dict] = field(default_factory=dict)
    # Preisliste (fuer Shops/Tavernen)
    price_list_file: Optional[str] = None
    # Zusaetzliche Bilder (Galerie)
    images: List[str] = field(default_factory=list)
    # Eigene Unter-Karte fuer diesen Ort
    sub_map: Optional[str] = None
    # Zusaetzliche Infos
    actions_available: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['triggers'] = [t.to_dict() if isinstance(t, Trigger) else t for t in self.triggers]
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'Location':
        data = dict(data)
        if 'triggers' in data:
            data['triggers'] = [Trigger.from_dict(t) if isinstance(t, dict) else t for t in data['triggers']]
        if 'map_position' in data and isinstance(data['map_position'], list):
            data['map_position'] = tuple(data['map_position'])
        return cls(**_filter_dataclass_fields(cls, data))


@dataclass
class WorldSettings:
    """Welteinstellungen"""
    name: str = "Neue Welt"
    description: str = ""
    genre: str = "Fantasy"
    # Zeit
    day_hours: int = 24
    daylight_hours: int = 12
    time_ratio: float = 1.0
    current_time: float = 12.0
    current_day: int = 1
    # Wahrscheinlichkeiten
    war_probability: float = 0.01
    disaster_probability: float = 0.005
    # Massstab
    map_scale_km_per_cm: float = 10.0
    # Simulation
    simulate_time: bool = True
    simulate_wear: bool = True
    simulate_hunger: bool = True
    simulate_disasters: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'WorldSettings':
        return cls(**_filter_dataclass_fields(cls, data))


@dataclass
class World:
    """Komplette Spielwelt"""
    id: str
    settings: WorldSettings = field(default_factory=WorldSettings)
    # Entitaeten
    locations: Dict[str, Location] = field(default_factory=dict)
    nations: Dict[str, Nation] = field(default_factory=dict)
    races: Dict[str, Race] = field(default_factory=dict)
    professions: List[str] = field(default_factory=list)
    social_classes: List[str] = field(default_factory=list)
    road_types: Dict[str, RoadType] = field(default_factory=dict)
    # Kampf
    weapons: Dict[str, Weapon] = field(default_factory=dict)
    armors: Dict[str, Armor] = field(default_factory=dict)
    combat_techniques: Dict[str, CombatTechnique] = field(default_factory=dict)
    spells: Dict[str, Spell] = field(default_factory=dict)
    dice_rules: Dict[str, DiceRule] = field(default_factory=dict)
    # Items
    item_classes: List[str] = field(default_factory=list)
    typical_items: Dict[str, Item] = field(default_factory=dict)
    # Fahrzeuge
    vehicles: Dict[str, Vehicle] = field(default_factory=dict)
    # Faehigkeiten (pro Welt definierbar)
    skill_definitions: Dict[str, dict] = field(default_factory=dict)
    # Karte
    map_image: Optional[str] = None
    # Multi-Map-System
    maps: Dict[str, GameMap] = field(default_factory=dict)
    active_map_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'settings': self.settings.to_dict(),
            'locations': {k: v.to_dict() for k, v in self.locations.items()},
            'nations': {k: v.to_dict() for k, v in self.nations.items()},
            'races': {k: v.to_dict() for k, v in self.races.items()},
            'professions': self.professions,
            'social_classes': self.social_classes,
            'road_types': {k: v.to_dict() for k, v in self.road_types.items()},
            'weapons': {k: v.to_dict() for k, v in self.weapons.items()},
            'armors': {k: v.to_dict() for k, v in self.armors.items()},
            'combat_techniques': {k: v.to_dict() for k, v in self.combat_techniques.items()},
            'spells': {k: v.to_dict() for k, v in self.spells.items()},
            'dice_rules': {k: v.to_dict() for k, v in self.dice_rules.items()},
            'item_classes': self.item_classes,
            'typical_items': {k: v.to_dict() for k, v in self.typical_items.items()},
            'vehicles': {k: v.to_dict() for k, v in self.vehicles.items()},
            'skill_definitions': self.skill_definitions,
            'map_image': self.map_image,
            'maps': {k: v.to_dict() for k, v in self.maps.items()},
            'active_map_id': self.active_map_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'World':
        maps = {k: GameMap.from_dict(v) for k, v in data.get('maps', {}).items()}
        active_map_id = data.get('active_map_id')
        map_image = data.get('map_image')
        # Migration: altes map_image -> neue GameMap
        if map_image and not maps:
            migrate_id = generate_short_id()
            maps[migrate_id] = GameMap(id=migrate_id, name="Weltkarte", background_image=map_image)
            active_map_id = migrate_id
        return cls(
            id=data['id'],
            settings=WorldSettings.from_dict(data.get('settings', {})),
            locations={k: Location.from_dict(v) for k, v in data.get('locations', {}).items()},
            nations={k: Nation.from_dict(v) for k, v in data.get('nations', {}).items()},
            races={k: Race.from_dict(v) for k, v in data.get('races', {}).items()},
            professions=data.get('professions', []),
            social_classes=data.get('social_classes', []),
            road_types={k: RoadType.from_dict(v) for k, v in data.get('road_types', {}).items()},
            weapons={k: Weapon.from_dict(v) for k, v in data.get('weapons', {}).items()},
            armors={k: Armor.from_dict(v) for k, v in data.get('armors', {}).items()},
            combat_techniques={k: CombatTechnique.from_dict(v) for k, v in data.get('combat_techniques', {}).items()},
            spells={k: Spell.from_dict(v) for k, v in data.get('spells', {}).items()},
            dice_rules={k: DiceRule.from_dict(v) for k, v in data.get('dice_rules', {}).items()},
            item_classes=data.get('item_classes', []),
            typical_items={k: Item.from_dict(v) for k, v in data.get('typical_items', {}).items()},
            vehicles={k: Vehicle.from_dict(v) for k, v in data.get('vehicles', {}).items()},
            skill_definitions=data.get('skill_definitions', {}),
            map_image=map_image,
            maps=maps,
            active_map_id=active_map_id
        )
