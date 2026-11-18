import colorsys
import sys
import traceback
import math
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGraphicsItem
)

from super_main import create_areas
from load_analysis import LoadViewer

EXTRA_COLUMNS = ["Lunghezza [m]", "Area influenza [m²]", "Carico lineare [kN/m]"]
TYPE_LABELS = {"Room": "Stanze", "Stairs": "Scale", "Other": "Aggetti"}

def _ring_to_qpolygon(ring) -> QPolygonF:
    x, y = ring.xy
    return QPolygonF([QPointF(float(px), float(-py)) for px, py in zip(x, y)])


def shapely_to_qpath(poly: Polygon) -> QPainterPath:
    """Poligono con eventuali buchi (riempimento even-odd)."""
    path = QPainterPath()
    path.setFillRule(Qt.FillRule.OddEvenFill)
    path.addPolygon(_ring_to_qpolygon(poly.exterior))
    path.closeSubpath()
    for ring in poly.interiors:
        path.addPolygon(_ring_to_qpolygon(ring))
        path.closeSubpath()
    return path


def iter_polygons(geometry):
    """Estrae tutti i poligoni, anche da GeometryCollection (anche annidate)."""
    if geometry is None or geometry.is_empty:
        return
    if isinstance(geometry, Polygon):
        yield geometry
    elif hasattr(geometry, "geoms"):          # Multi* e GeometryCollection
        for g in geometry.geoms:
            yield from iter_polygons(g)


def iter_regions(true_regions):
    """
    Restituisce coppie (ID regione, geometria).
    Accetta il nuovo formato (dict {ID regione: Polygon}) e,
    per compatibilità, anche un singolo poligono.
    """
    if true_regions is None:
        return
    if isinstance(true_regions, dict):
        yield from true_regions.items()
    elif not getattr(true_regions, "is_empty", True):
        yield "—", true_regions


def build_struct_colors(struct_ids):
    """Un colore distinto per ogni elemento strutturale (hue con rapporto aureo)."""
    colors = {}
    golden = 0.618033988749895
    for i, struct_id in enumerate(struct_ids):
        hue = (i * golden) % 1.0
        saturation = 0.65 if i % 2 == 0 else 0.85
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, 0.95)
        colors[struct_id] = QColor(int(r * 255), int(g * 255), int(b * 255))
    return colors


class AreaViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analisi aree strutturali")
        self.resize(1600, 900)

        self.dataframe = None
        self.dxf_path = None
        self.fill_alpha = 120
        self.struct_colors = {}

        self._build_ui()
        self._update_controls_state()

    def check_regions(self):
        problems = []
        n_regions = 0
        for _, row in self.dataframe.iterrows():
            struct_id = row["Struct ID"]
            regions = list(iter_regions(row["True Regions"]))
            if not regions:
                problems.append(f"{struct_id}: nessuna regione")
                continue
            for region_id, geom in regions:
                n_regions += 1
                if geom is None or geom.is_empty:
                    problems.append(f"{struct_id}/{region_id}: vuota")
                    continue
                polys = list(iter_polygons(geom))
                if not polys:
                    problems.append(f"{struct_id}/{region_id}: tipo {geom.geom_type} senza poligoni")
                    continue
                drawn = sum(p.area for p in polys)
                if abs(drawn - geom.area) > 1e-6 * max(geom.area, 1.0):
                    problems.append(f"{struct_id}/{region_id}: area disegnata {drawn:.3f} su {geom.area:.3f}")

        if problems:
            text = f"<b>Controllo regioni:</b> {len(problems)} problemi su {n_regions}<br>" + "<br>".join(problems[:15])
            print("\n".join(problems))
        else:
            text = f"<b>Controllo regioni:</b> tutte le {n_regions} regioni sono disegnabili."
        self.check_label.setText(text)

    def _build_ui(self):
        central = QWidget()
        root_layout = QVBoxLayout(central)

        # ---------- Barra superiore ----------
        top_bar = QHBoxLayout()

        self.open_button = QPushButton("Apri file DXF…")
        self.open_button.clicked.connect(self.open_dxf)

        self.file_label = QLabel("Nessun file selezionato")
        self.file_label.setStyleSheet("color: gray;")

        top_bar.addWidget(self.open_button)
        top_bar.addWidget(self.file_label, stretch=1)
        root_layout.addLayout(top_bar)

        # ---------- Splitter principale ----------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1) Plot
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints().__class__.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.splitter.addWidget(self.view)

        # 2) Tabella
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(4, 4, 4, 4)

        table_title = QLabel("<b>Informazioni aree</b>")
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self.on_table_selection)

        table_layout.addWidget(table_title)
        table_layout.addWidget(self.table)
        self.splitter.addWidget(table_container)

        # 3) Pannello controlli
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(8, 8, 8, 8)

        # Parametri di calcolo
        params_box = QGroupBox("Parametri divisione aree")
        params_form = QFormLayout(params_box)

        self.buffer_spin = QDoubleSpinBox()
        self.buffer_spin.setRange(0.0, 10000.0)
        self.buffer_spin.setValue(30.0)

        self.stretch_spin = QDoubleSpinBox()
        self.stretch_spin.setRange(0.01, 1000.0)
        self.stretch_spin.setValue(2.5)
        self.stretch_spin.setDecimals(2)

        params_form.addRow("Buffer:", self.buffer_spin)
        params_form.addRow("Stretch:", self.stretch_spin)

        self.reload_button = QPushButton("Ricalcola aree")
        self.reload_button.clicked.connect(self.recalculate_areas)

        # Visualizzazione
        display_box = QGroupBox("Elementi da visualizzare")
        display_layout = QVBoxLayout(display_box)

        self.show_regions_check = QCheckBox("True Regions")
        self.show_regions_check.setChecked(True)
        self.show_regions_check.toggled.connect(self.refresh_plot)

        self.show_struct_check = QCheckBox("Struct Polygon")
        self.show_struct_check.setChecked(False)
        self.show_struct_check.toggled.connect(self.refresh_plot)

        self.show_buffer_check = QCheckBox("True Struct Buffer Polygon")
        self.show_buffer_check.setChecked(False)
        self.show_buffer_check.toggled.connect(self.refresh_plot)

        self.show_rooms_check = QCheckBox("Stanze / SCALE / AGGETTI")
        self.show_rooms_check.setChecked(False)
        self.show_rooms_check.toggled.connect(self.refresh_plot)

        # I colori ora sono assegnati per elemento strutturale:
        # resta regolabile solo la trasparenza del riempimento.
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(10, 255)
        self.alpha_slider.setValue(self.fill_alpha)
        self.alpha_slider.valueChanged.connect(self.change_alpha)

        display_layout.addWidget(self.show_regions_check)
        display_layout.addWidget(self.show_struct_check)
        display_layout.addWidget(self.show_buffer_check)
        display_layout.addWidget(self.show_rooms_check)
        display_layout.addWidget(QLabel("Opacità riempimento:"))
        display_layout.addWidget(self.alpha_slider)

        info_box = QGroupBox("Informazioni")
        info_layout = QVBoxLayout(info_box)
        self.info_label = QLabel("Nessuna area selezionata.")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        self.check_label = QLabel("")
        self.check_label.setWordWrap(True)
        info_layout.addWidget(self.check_label)
        controls_layout.addWidget(params_box)
        controls_layout.addWidget(self.reload_button)
        controls_layout.addWidget(display_box)
        #----------------------------------------------------
        loads_box = QGroupBox("Carichi")
        loads_form = QFormLayout(loads_box)
        self.load_spins = {}
        for key, default in (("Room", 2.0), ("Stairs", 4.0), ("Other", 4.0)):
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1000.0)
            spin.setDecimals(2)
            spin.setSingleStep(0.5)
            spin.setSuffix(" kN/m²")
            spin.setValue(default)
            spin.valueChanged.connect(self.update_loads)
            self.load_spins[key] = spin
            loads_form.addRow(f"{TYPE_LABELS[key]}:", spin)

        self.unit_spin = QDoubleSpinBox()
        self.unit_spin.setDecimals(6)
        self.unit_spin.setRange(0.000001, 1000.0)
        self.unit_spin.setValue(0.01)          # 1 unità disegno = 0.01 m (disegno in cm)
        self.unit_spin.valueChanged.connect(self.update_loads)
        loads_form.addRow("Unità disegno → m:", self.unit_spin)

        self.show_loads_check = QCheckBox("Mostra carico lineare sul disegno")
        self.show_loads_check.toggled.connect(self.refresh_plot)
        loads_form.addRow(self.show_loads_check)

        self.loads_calculator_button = QPushButton("Analisi dei carichi...") ########################################################################
        self.loads_calculator_button.clicked.connect(self._load_analysis)
        loads_form.addRow(self.loads_calculator_button)

        controls_layout.addWidget(loads_box)
        #----------------------------------------------------
        controls_layout.addWidget(info_box)
        controls_layout.addStretch()

        self.splitter.addWidget(controls_container)

        self.splitter.setSizes([900, 420, 280])
        root_layout.addWidget(self.splitter, stretch=1)

        self.setCentralWidget(central)

    # ========================================================
    # Caricamento e calcolo
    # ========================================================
    def _load_analysis(self):
        
        # mantiene un riferimento alla finestra, altrimenti viene distrutta
        if not hasattr(self, "_load_window") or self._load_window is None:
            self._load_window = LoadViewer()
        self._load_window.show()
        self._load_window.raise_()
        self._load_window.activateWindow()


    def open_dxf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file DXF",
            "",
            "DXF files (*.dxf);;All files (*)",
        )

        if not path:
            return

        self.dxf_path = path
        self.file_label.setText(path)
        self.calculate_areas()

    def recalculate_areas(self):
        if self.dxf_path is None:
            QMessageBox.information(self, "Nessun file", "Seleziona prima un file DXF.")
            return

        self.calculate_areas()

    def calculate_areas(self):
        buffer_value = float(self.buffer_spin.value())
        stretch_value = float(self.stretch_spin.value())

        try:
            self.dataframe = create_areas(
                self.dxf_path,
                buffer=buffer_value,
                stretch=stretch_value,
            )
        except Exception:
            error_text = traceback.format_exc()
            QMessageBox.critical(self, "Errore", f"Errore durante il calcolo:\n\n{error_text}")
            return

        # Un colore per ogni elemento strutturale
        self.struct_colors = build_struct_colors(list(self.dataframe["Struct ID"]))

        self.compute_loads()
        self._update_controls_state()
        self.update_table()
        self.check_regions()
        self.refresh_plot()

    def _update_controls_state(self):
        has_data = self.dataframe is not None
        self.reload_button.setEnabled(has_data)
        self.show_regions_check.setEnabled(has_data)
        self.show_struct_check.setEnabled(has_data)
        self.show_buffer_check.setEnabled(has_data)
        self.show_rooms_check.setEnabled(has_data)

    # --------------------------------------------------------

    def compute_loads(self):
        """carico lineare = Σ(q_tipo · area_tipo) / lunghezza"""
        self.loads = {}
        if self.dataframe is None:
            return

        room_types = self.dataframe.attrs.get("room_types", {})
        q = {key: spin.value() for key, spin in self.load_spins.items()}
        f = self.unit_spin.value()

        for _, row in self.dataframe.iterrows():
            length = float(row["Length"]) * f
            area_by_type = {key: 0.0 for key in q}
            total_area = 0.0
            force = 0.0

            for region_id, geom in iter_regions(row["True Regions"]):
                if geom is None or geom.is_empty:
                    continue
                area = geom.area * f * f
                total_area += area
                rtype = room_types.get(region_id)      # "Extra" -> None -> carico 0
                if rtype in q:
                    area_by_type[rtype] += area
                    force += q[rtype] * area

            self.loads[row["Struct ID"]] = {
                "length": length,
                "area": total_area,
                "area_by_type": area_by_type,
                "force": force,
                "line": force / length if length > 0 else float("nan"),
            }

    def update_loads(self):
        if self.dataframe is None:
            return
        self.compute_loads()
        self.update_table()
        if self.show_loads_check.isChecked():
            self.refresh_plot()

    def _load_html(self, struct_id):
        res = self.loads.get(struct_id)
        if res is None:
            return ""
        lines = []
        for key, area in res["area_by_type"].items():
            q = self.load_spins[key].value()
            lines.append(f"&nbsp;&nbsp;{TYPE_LABELS[key]}: {area:.2f} m² × {q:.2f} = {q * area:.2f} kN")
        return (
            f"<br><b>Lunghezza:</b> {res['length']:.2f} m"
            f"<br><b>Area di influenza:</b> {res['area']:.2f} m²"
            f"<br><b>Contributi:</b><br>" + "<br>".join(lines) +
            f"<br><b>Carico totale:</b> {res['force']:.2f} kN"
            f"<br><b>Carico lineare:</b> {res['line']:.2f} kN/m"
        )

    # --------------------------------------------------------


    # ========================================================
    # Tabella
    # ========================================================
    def update_table(self):
        selected = self.table.currentRow()
        self.table.clear()
        self.table.setRowCount(0)

        if self.dataframe is None or self.dataframe.empty:
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Nessun dato"])
            return

        columns = ["Struct ID", "Text", "Associated Bound", "Associated Rooms"]
        available_columns = [col for col in columns if col in self.dataframe.columns]
        headers = available_columns + EXTRA_COLUMNS
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row_index, (_, row) in enumerate(self.dataframe.iterrows()):
            self.table.insertRow(row_index)

            for col_index, column in enumerate(available_columns):
                value = row[column]
                if isinstance(value, (list, tuple)):
                    value = ", ".join(str(item) for item in value)

                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, row_index)

                if column == "Struct ID":
                    color = self.struct_colors.get(row["Struct ID"])
                    if color is not None:
                        bg = QColor(color)
                        bg.setAlpha(160)
                        item.setBackground(QBrush(bg))
                        item.setForeground(QBrush(QColor(0, 0, 0)))

                self.table.setItem(row_index, col_index, item)

            # colonne dei carichi
            res = self.loads.get(row["Struct ID"])
            values = ["—"] * 3 if res is None else [
                f"{res['length']:.2f}", f"{res['area']:.2f}", f"{res['line']:.2f}"
            ]
            for k, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, row_index)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, len(available_columns) + k, item)

        self.table.resizeColumnsToContents()
        if 0 <= selected < self.table.rowCount():
            self.table.selectRow(selected)

    def on_table_selection(self):
        selected_rows = {index.row() for index in self.table.selectedIndexes()}

        if not selected_rows or self.dataframe is None:
            self.info_label.setText("Nessuna area selezionata.")
            return

        row = next(iter(selected_rows))
        if row >= len(self.dataframe):
            return

        data = self.dataframe.iloc[row]
        struct_id = data.get("Struct ID", "—")
        text = data.get("Text", "—")

        regions_text = "—"
        if "True Regions" in self.dataframe.columns:
            lines = []
            total = 0.0
            for region_id, geometry in iter_regions(data["True Regions"]):
                if geometry is None or geometry.is_empty:
                    continue
                total += geometry.area
                lines.append(f"&nbsp;&nbsp;{region_id}: {geometry.area:.3f}")
            if lines:
                regions_text = "<br>" + "<br>".join(lines) + f"<br><b>Totale:</b> {total:.3f}"

        self.info_label.setText(
            f"<b>Struct ID:</b> {struct_id}<br>"
            f"<b>Testo:</b> {text}<br>"
            f"<b>Aree True Regions:</b> {regions_text}"
            + self._load_html(struct_id)
        )

    # ========================================================
    # Plot
    # ========================================================
    def refresh_plot(self):
        self.scene.clear()

        if self.dataframe is None:
            return

        if self.show_regions_check.isChecked() and "True Regions" in self.dataframe.columns:
            for _, row in self.dataframe.iterrows():
                base_color = self.struct_colors.get(row["Struct ID"], QColor(80, 160, 255))

                brush = QColor(base_color)
                brush.setAlpha(self.fill_alpha)
                pen = base_color.darker(160)

                for region_id, geometry in iter_regions(row["True Regions"]):
                    for polygon in iter_polygons(geometry):
                        self.scene.addPath(shapely_to_qpath(polygon), pen=pen, brush=brush)

        if self.show_struct_check.isChecked() and "Struct Polygon" in self.dataframe.columns:
            transparent_brush = QColor(255, 255, 255, 0)

            for geometry in self.dataframe["Struct Polygon"]:
                for polygon in iter_polygons(geometry):
                    self.scene.addPath(
                        shapely_to_qpath(polygon),
                        pen=QColor(200, 0, 0),
                        brush=transparent_brush,
                    )

        if self.show_buffer_check.isChecked() and "True Struct Buffer Polygon" in self.dataframe.columns:
            buffer_brush = QColor(255, 200, 0, 70)

            for geometry in self.dataframe["True Struct Buffer Polygon"]:
                for polygon in iter_polygons(geometry):
                    self.scene.addPath(
                        shapely_to_qpath(polygon),
                        pen=QColor(180, 120, 0),
                        brush=buffer_brush,
                    )

        if self.show_loads_check.isChecked():
            for _, row in self.dataframe.iterrows():
                res = self.loads.get(row["Struct ID"])
                if res is None or math.isnan(res["line"]):
                    continue
                c = row["Centroid"]
                label = self.scene.addSimpleText(f"{res['line']:.1f}")
                label.setBrush(QBrush(QColor(0, 0, 0)))
                label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)  # dimensione costante con lo zoom
                label.setPos(c.x, -c.y)


        self.view.fitInView(
            self.scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def change_alpha(self, value):
        self.fill_alpha = int(value)
        self.refresh_plot()


def this_main():
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    window = AreaViewer()
    window.show()

    if not getattr(app, "_area_viewer_running", False):
        app._area_viewer_running = True
        app.exec()


if __name__ == "__main__":
    this_main()