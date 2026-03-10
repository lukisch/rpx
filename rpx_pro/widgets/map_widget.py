"""MapWidget: Interaktive Kartenansicht mit verschiebbaren Markern und Zeichenwerkzeugen."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from PySide6.QtCore import Signal, Qt, QRectF, QPointF
from PySide6.QtGui import (
    QColor, QBrush, QPen, QFont, QPainter, QPixmap,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMenu, QInputDialog, QFileDialog,
    QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
    QGraphicsPixmapItem,
)

from rpx_pro.constants import generate_short_id
from rpx_pro.models.entities import MapElement


class CharacterMarker(QGraphicsEllipseItem):
    """Verschiebbarer Charakter-Marker auf der Karte"""

    def __init__(self, char_id: str, char_name: str, color: QColor, x: float, y: float):
        super().__init__(-12, -12, 24, 24)
        self.char_id = char_id
        self.char_name = char_name
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#fff"), 2))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setPos(x, y)
        self.setZValue(10)
        self.setToolTip(char_name)

        self._label = QGraphicsTextItem(char_name, self)
        self._label.setDefaultTextColor(QColor("#fff"))
        font = QFont("Arial", 9, QFont.Bold)
        self._label.setFont(font)
        self._label.setPos(-len(char_name) * 3, 14)


class LocationMarker(QGraphicsEllipseItem):
    """Verschiebbarer Ort-Marker auf der Karte mit Farbschema nach Typ"""

    TYPE_COLORS = {
        "city": ("#e74c3c", "#c0392b"),
        "river": ("#3498db", "#2980b9"),
        "anomaly": ("#3498db", "#2980b9"),
        "mountain": ("#95a5a6", "#7f8c8d"),
        "region": ("#95a5a6", "#7f8c8d"),
        "forest": ("#2ecc71", "#27ae60"),
        "building": ("#f1c40f", "#f39c12"),
        "ship": ("#f1c40f", "#f39c12"),
    }

    def __init__(self, loc_id: str, loc_name: str, x: float, y: float, loc_type: str = "city"):
        super().__init__(-6, -6, 12, 12)
        self.loc_id = loc_id
        self.loc_name = loc_name
        self.loc_type = loc_type
        colors = self.TYPE_COLORS.get(loc_type, ("#e67e22", "#f39c12"))
        fill_color, border_color = colors
        self.setBrush(QBrush(QColor(fill_color)))
        self.setPen(QPen(QColor(border_color), 1.5))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setPos(x, y)
        self.setZValue(5)
        self.setToolTip(f"{loc_name} ({loc_type})")

        self._label = QGraphicsTextItem(loc_name, self)
        self._label.setDefaultTextColor(QColor(fill_color))
        font = QFont("Arial", 8)
        self._label.setFont(font)
        self._label.setPos(8, -8)


class ResizeHandle(QGraphicsRectItem):
    """Kleiner Griff zum Resizen von Zeichenelementen"""

    def __init__(self, parent_item, corner: str):
        super().__init__(-4, -4, 8, 8, parent_item)
        self._corner = corner
        self._parent = parent_item
        self.setBrush(QBrush(QColor("#3498db")))
        self.setPen(QPen(QColor("#fff"), 1))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setZValue(20)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged and self._parent:
            pos = self.pos()
            if self._corner == "br":
                new_w = max(20, pos.x())
                new_h = max(20, pos.y())
                self._parent.setRect(0, 0, new_w, new_h)
        return super().itemChange(change, value)


class MapWidget(QWidget):
    """Interaktive Kartenansicht mit verschiebbaren Markern und Zeichenwerkzeugen"""

    location_clicked = Signal(str)
    marker_moved = Signal(str, float, float)
    element_added = Signal(str, dict)
    element_moved = Signal(str, float, float)
    element_resized = Signal(str, float, float)
    map_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._char_markers: Dict[str, CharacterMarker] = {}
        self._loc_markers: Dict[str, LocationMarker] = {}
        self._map_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._grid_lines = []
        self._draw_elements: Dict[str, Any] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#0a0a1a")))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setStyleSheet("QGraphicsView { border: none; background: #0a0a1a; }")
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setInteractive(True)
        self.view.viewport().installEventFilter(self)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.view)

    def eventFilter(self, obj, event):
        if obj == self.view.viewport() and event.type() == event.Type.Wheel:
            factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
            self.view.scale(factor, factor)
            return True
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        self.view.scale(factor, factor)

    def load_map(self, map_path: str):
        """Laedt ein Kartenbild als Hintergrund oder zeigt Grid"""
        for line in self._grid_lines:
            self.scene.removeItem(line)
        self._grid_lines.clear()

        if self._map_pixmap_item:
            self.scene.removeItem(self._map_pixmap_item)
            self._map_pixmap_item = None

        if map_path and Path(map_path).exists():
            pixmap = QPixmap(map_path)
            self._map_pixmap_item = self.scene.addPixmap(pixmap)
            self._map_pixmap_item.setZValue(0)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
        else:
            w, h = 1200, 900
            self.scene.setSceneRect(QRectF(0, 0, w, h))
            pen = QPen(QColor("#1a1a2e"), 1)
            for x in range(0, w + 1, 50):
                line = self.scene.addLine(x, 0, x, h, pen)
                line.setZValue(0)
                self._grid_lines.append(line)
            for y in range(0, h + 1, 50):
                line = self.scene.addLine(0, y, w, y, pen)
                line.setZValue(0)
                self._grid_lines.append(line)
            pen_major = QPen(QColor("#2a2a3e"), 2)
            for x in range(0, w + 1, 200):
                line = self.scene.addLine(x, 0, x, h, pen_major)
                line.setZValue(1)
                self._grid_lines.append(line)
            for y in range(0, h + 1, 200):
                line = self.scene.addLine(0, y, w, y, pen_major)
                line.setZValue(1)
                self._grid_lines.append(line)

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def set_characters(self, characters: Dict[str, Any]):
        """Setzt Charakter-Marker auf die Karte"""
        for marker in self._char_markers.values():
            self.scene.removeItem(marker)
        self._char_markers.clear()

        colors = [QColor("#e74c3c"), QColor("#2ecc71"), QColor("#3498db"),
                  QColor("#9b59b6"), QColor("#f1c40f"), QColor("#1abc9c")]
        rect = self.scene.sceneRect()
        cx, cy = rect.width() / 2, rect.height() / 2
        for i, (char_id, data) in enumerate(characters.items()):
            color = colors[i % len(colors)]
            x = data.get("map_x", cx - 100 + i * 60)
            y = data.get("map_y", cy)
            marker = CharacterMarker(char_id, data.get("name", "?"), color, x, y)
            self.scene.addItem(marker)
            self._char_markers[char_id] = marker

    def set_locations(self, locations: Dict[str, Any]):
        """Setzt Ort-Marker auf die Karte"""
        for marker in self._loc_markers.values():
            self.scene.removeItem(marker)
        self._loc_markers.clear()

        default_spacing = 100
        for i, (loc_id, data) in enumerate(locations.items()):
            pos = data.get("map_position", (0, 0))
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                x, y = float(pos[0]), float(pos[1])
            else:
                x, y = 0.0, 0.0
            if x == 0 and y == 0:
                x = 100 + (i % 6) * default_spacing
                y = 100 + (i // 6) * default_spacing
            marker = LocationMarker(loc_id, data.get("name", "?"), x, y, data.get("location_type", "city"))
            self.scene.addItem(marker)
            self._loc_markers[loc_id] = marker

    def get_character_positions(self) -> Dict[str, Tuple[float, float]]:
        """Gibt die aktuellen Positionen aller Charakter-Marker zurueck"""
        positions = {}
        for char_id, marker in self._char_markers.items():
            pos = marker.pos()
            positions[char_id] = (pos.x(), pos.y())
        return positions

    def _show_context_menu(self, pos):
        scene_pos = self.view.mapToScene(pos)
        menu = QMenu(self)
        menu.addAction("Kreis hinzufuegen", lambda: self.add_element("circle", scene_pos))
        menu.addAction("Rechteck hinzufuegen", lambda: self.add_element("rect", scene_pos))
        menu.addAction("Text hinzufuegen", lambda: self.add_element("text", scene_pos))
        menu.addAction("Linie hinzufuegen", lambda: self.add_element("line", scene_pos))
        menu.addAction("Gestrichelte Linie hinzufuegen", lambda: self.add_element("dashed_line", scene_pos))
        menu.addAction("Bild importieren...", lambda: self._import_image_element(scene_pos))
        menu.addSeparator()
        selected = self.scene.selectedItems()
        del_action = menu.addAction("Element loeschen")
        del_action.setEnabled(bool(selected))
        del_action.triggered.connect(self._delete_selected_elements)
        menu.exec(self.view.mapToGlobal(pos))

    def add_element(self, element_type: str, pos: QPointF) -> str:
        elem_id = generate_short_id()
        color = QColor("#e67e22")
        item = None

        if element_type == "circle":
            item = QGraphicsEllipseItem(0, 0, 80, 80)
            item.setBrush(QBrush(QColor(color.name() + "40")))
            item.setPen(QPen(color, 2))
        elif element_type == "rect":
            item = QGraphicsRectItem(0, 0, 100, 70)
            item.setBrush(QBrush(QColor(color.name() + "40")))
            item.setPen(QPen(color, 2))
        elif element_type == "text":
            text, ok = QInputDialog.getText(self, "Text eingeben", "Text:")
            if not ok or not text:
                return ""
            item = QGraphicsTextItem(text)
            item.setDefaultTextColor(color)
            font = QFont("Arial", 14)
            item.setFont(font)
            item.setTextInteractionFlags(Qt.TextEditorInteraction)
        elif element_type in ("line", "dashed_line"):
            item = QGraphicsLineItem(0, 0, 150, 0)
            pen = QPen(color, 2)
            if element_type == "dashed_line":
                pen.setStyle(Qt.DashLine)
            item.setPen(pen)
        elif element_type == "image":
            return ""

        if item:
            item.setFlag(item.ItemIsMovable, True)
            item.setFlag(item.ItemIsSelectable, True)
            item.setFlag(item.ItemSendsGeometryChanges, True)
            item.setPos(pos)
            item.setZValue(3)
            item.setData(0, elem_id)
            item.setData(1, element_type)
            self.scene.addItem(item)
            self._draw_elements[elem_id] = item

            if element_type in ("rect", "circle"):
                w = 100 if element_type == "rect" else 80
                h = 70 if element_type == "rect" else 80
                handle = ResizeHandle(item, "br")
                handle.setPos(w, h)

            self.element_added.emit(elem_id, {"type": element_type})
            self.map_changed.emit()
            return elem_id
        return ""

    def _import_image_element(self, pos: QPointF):
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild importieren", "",
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not path:
            return
        elem_id = generate_short_id()
        pixmap = QPixmap(path)
        if pixmap.width() > 300:
            pixmap = pixmap.scaledToWidth(300, Qt.SmoothTransformation)
        item = QGraphicsPixmapItem(pixmap)
        item.setFlag(item.ItemIsMovable, True)
        item.setFlag(item.ItemIsSelectable, True)
        item.setFlag(item.ItemSendsGeometryChanges, True)
        item.setPos(pos)
        item.setZValue(3)
        item.setData(0, elem_id)
        item.setData(1, "image")
        item.setData(2, path)
        self.scene.addItem(item)
        self._draw_elements[elem_id] = item
        self.element_added.emit(elem_id, {"type": "image", "path": path})
        self.map_changed.emit()

    def _delete_selected_elements(self):
        for item in self.scene.selectedItems():
            elem_id = item.data(0)
            if elem_id and elem_id in self._draw_elements:
                self.scene.removeItem(item)
                del self._draw_elements[elem_id]
        self.map_changed.emit()

    def clear_draw_elements(self):
        for item in list(self._draw_elements.values()):
            self.scene.removeItem(item)
        self._draw_elements.clear()

    def load_elements(self, elements: Dict[str, MapElement]):
        """Laedt Zeichenelemente aus MapElement-Dicts"""
        self.clear_draw_elements()
        for elem_id, elem in elements.items():
            color = QColor(elem.color)
            item = None
            if elem.element_type == "circle":
                item = QGraphicsEllipseItem(0, 0, elem.width, elem.height)
                if elem.fill_color:
                    item.setBrush(QBrush(QColor(elem.fill_color)))
                else:
                    item.setBrush(QBrush(QColor(elem.color + "40")))
                item.setPen(QPen(color, elem.line_width))
            elif elem.element_type == "rect":
                item = QGraphicsRectItem(0, 0, elem.width, elem.height)
                if elem.fill_color:
                    item.setBrush(QBrush(QColor(elem.fill_color)))
                else:
                    item.setBrush(QBrush(QColor(elem.color + "40")))
                item.setPen(QPen(color, elem.line_width))
            elif elem.element_type == "text":
                item = QGraphicsTextItem(elem.text)
                item.setDefaultTextColor(color)
                item.setFont(QFont("Arial", elem.font_size))
                item.setTextInteractionFlags(Qt.TextEditorInteraction)
            elif elem.element_type in ("line", "dashed_line"):
                item = QGraphicsLineItem(0, 0, elem.x2 - elem.x, elem.y2 - elem.y)
                pen = QPen(color, elem.line_width)
                if elem.element_type == "dashed_line":
                    pen.setStyle(Qt.DashLine)
                item.setPen(pen)
            elif elem.element_type == "image" and elem.image_path:
                pixmap = QPixmap(elem.image_path)
                if not pixmap.isNull():
                    if elem.width and elem.width != 100:
                        pixmap = pixmap.scaledToWidth(int(elem.width), Qt.SmoothTransformation)
                    item = QGraphicsPixmapItem(pixmap)
                    item.setData(2, elem.image_path)

            if item:
                item.setFlag(item.ItemIsMovable, True)
                item.setFlag(item.ItemIsSelectable, True)
                item.setFlag(item.ItemSendsGeometryChanges, True)
                item.setPos(elem.x, elem.y)
                item.setZValue(3)
                item.setOpacity(elem.opacity)
                item.setRotation(elem.rotation)
                item.setData(0, elem_id)
                item.setData(1, elem.element_type)
                self.scene.addItem(item)
                self._draw_elements[elem_id] = item

                if elem.element_type in ("rect", "circle"):
                    handle = ResizeHandle(item, "br")
                    handle.setPos(elem.width, elem.height)

    def get_elements(self) -> Dict[str, MapElement]:
        """Liest aktuelle Zeichenelemente als MapElement-Dict zurueck"""
        result = {}
        for elem_id, item in self._draw_elements.items():
            pos = item.pos()
            etype = item.data(1) or "rect"
            elem = MapElement(
                id=elem_id,
                element_type=etype,
                x=pos.x(),
                y=pos.y(),
                rotation=item.rotation(),
                opacity=item.opacity()
            )
            if etype in ("rect", "circle"):
                r = item.rect()
                elem.width = r.width()
                elem.height = r.height()
                pen = item.pen()
                elem.color = pen.color().name()
                elem.line_width = pen.widthF()
                brush = item.brush()
                if brush.style() != Qt.NoBrush:
                    elem.fill_color = brush.color().name()
            elif etype == "text":
                elem.text = item.toPlainText()
                elem.font_size = item.font().pointSize()
                elem.color = item.defaultTextColor().name()
            elif etype in ("line", "dashed_line"):
                line = item.line()
                elem.x2 = pos.x() + line.x2()
                elem.y2 = pos.y() + line.y2()
                elem.color = item.pen().color().name()
                elem.line_width = item.pen().widthF()
            elif etype == "image":
                elem.image_path = item.data(2) or ""
                pm = item.pixmap()
                if not pm.isNull():
                    elem.width = pm.width()
                    elem.height = pm.height()
            result[elem_id] = elem
        return result

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene.sceneRect().width() > 0:
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
