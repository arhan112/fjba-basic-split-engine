
# ============================================================
# FjBa | BASIC ULTIMATE SPLIT ENGINE FOR QGIS
# Version 1.2.1 | Basic Edition
#
# FjBa metallic emerald / gold branding
# Animated metallic logo with light sweep
#
# Designed for QGIS 3.x (PyQt5) and QGIS 4.x (PyQt6) via qgis.PyQt
#
# GUI:
# - Standard minimize / maximize / close buttons
# - Resizable desktop window
# - Adaptive initial window size
# - Laptop-friendly minimum dimensions
# - Scrollable content area
#
# BASIC FEATURES
# - Multiple line layer selection
# - Multiple polygon layer selection
# - Polygon geometry repair
# - Polygon boundary extraction
# - Line splitting
# - Spatial index optimization
# - Polygon attribute transfer
# - Longest intersection assignment
# - Original attribute type preservation
# - Progress monitoring
# - Processing cancellation
# - Processing log
# - Memory output layer
#
# IMPORTANT:
# - Processing is synchronous in this edition; large jobs may temporarily
#   make the QGIS interface less responsive.
# - Static source review and syntax validation do not replace testing inside
#   each supported QGIS release.
#
# ============================================================

import datetime
import re
import traceback

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QVariant, QTimer
from qgis.PyQt.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QLinearGradient,
    QPen,
    QBrush
)

from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsSpatialIndex,
    QgsWkbTypes,
    QgsProcessingFeedback
)

import processing


# ============================================================
# QT COMPATIBILITY
# ============================================================
# Prefer scoped enums (PyQt6); fall back to legacy aliases (PyQt5).
# qgis.PyQt selects the Qt binding shipped with the running QGIS.

_QtWindowType = getattr(Qt, "WindowType", Qt)
_QtWidgetAttribute = getattr(Qt, "WidgetAttribute", Qt)
_QPainterRenderHint = getattr(QPainter, "RenderHint", QPainter)
_QFontWeight = getattr(QFont, "Weight", QFont)
_QtItemDataRole = getattr(Qt, "ItemDataRole", Qt)
_QtAlignmentFlag = getattr(Qt, "AlignmentFlag", Qt)
_QtScrollBarPolicy = getattr(Qt, "ScrollBarPolicy", Qt)
_QFrameShape = getattr(QtWidgets.QFrame, "Shape", QtWidgets.QFrame)
_QAbstractSelectionMode = getattr(
    QtWidgets.QAbstractItemView, "SelectionMode", QtWidgets.QAbstractItemView
)
_QMessageBoxButton = getattr(
    QtWidgets.QMessageBox, "StandardButton", QtWidgets.QMessageBox
)

WINDOW_MINIMIZE = _QtWindowType.WindowMinimizeButtonHint
WINDOW_MAXIMIZE = _QtWindowType.WindowMaximizeButtonHint
WINDOW_CLOSE = _QtWindowType.WindowCloseButtonHint
WINDOW_SYSTEM_MENU = _QtWindowType.WindowSystemMenuHint

WA_TRANSLUCENT = _QtWidgetAttribute.WA_TranslucentBackground
ANTIALIASING = _QPainterRenderHint.Antialiasing
FONT_BOLD = _QFontWeight.Bold
USER_ROLE = _QtItemDataRole.UserRole
ALIGN_CENTER = _QtAlignmentFlag.AlignCenter
SCROLLBAR_ALWAYS_OFF = _QtScrollBarPolicy.ScrollBarAlwaysOff
FRAME_NO_FRAME = _QFrameShape.NoFrame
MULTI_SELECTION = _QAbstractSelectionMode.MultiSelection
MESSAGE_YES = _QMessageBoxButton.Yes
MESSAGE_NO = _QMessageBoxButton.No

# ============================================================
# ANIMATED FjBa METALLIC LOGO
# ============================================================

class FjBaMetallicLogo(QtWidgets.QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.phase = 0.0

        self.setMinimumSize(80, 65)
        self.setMaximumSize(110, 90)

        self.setAttribute(
            WA_TRANSLUCENT,
            True
        )

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.advance_animation
        )

        self.timer.start(35)

    def advance_animation(self):

        self.phase = (
            self.phase + 0.018
        ) % 1.5

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            ANTIALIASING
        )

        rect = self.rect()

        font = QFont(
            "Segoe UI",
            27,
            FONT_BOLD
        )

        painter.setFont(font)

        text = "FjBa"

        metrics = painter.fontMetrics()

        if hasattr(metrics, "horizontalAdvance"):
            text_width = metrics.horizontalAdvance(text)
        else:
            text_width = metrics.width(text)

        x = (rect.width() - text_width) / 2

        baseline = rect.height() * 0.62

        path = QPainterPath()

        path.addText(
            x,
            baseline,
            font,
            text
        )

        gradient = QLinearGradient(
            0, 0,
            rect.width(),
            rect.height()
        )

        gradient.setColorAt(
            0.0, QColor("#FFF2B0")
        )

        gradient.setColorAt(
            0.22, QColor("#D5A832")
        )

        gradient.setColorAt(
            0.45, QColor("#F9E7A0")
        )

        gradient.setColorAt(
            0.68, QColor("#16A879")
        )

        gradient.setColorAt(
            1.0, QColor("#075C43")
        )

        painter.setPen(
            QPen(QColor("#B68A28"), 0.8)
        )

        painter.setBrush(
            QBrush(gradient)
        )

        painter.drawPath(path)

        # Animated light sweep

        sweep_x = self.phase * rect.width()

        sweep = QLinearGradient(
            sweep_x - 12,
            0,
            sweep_x + 12,
            0
        )

        sweep.setColorAt(
            0.0,
            QColor(255, 255, 255, 0)
        )

        sweep.setColorAt(
            0.5,
            QColor(255, 255, 255, 180)
        )

        sweep.setColorAt(
            1.0,
            QColor(255, 255, 255, 0)
        )

        painter.save()

        painter.setClipPath(path)

        painter.fillRect(
            rect,
            sweep
        )

        painter.restore()

        painter.end()

    def stop(self):

        if self.timer.isActive():
            self.timer.stop()


# ============================================================
# PROCESSING FEEDBACK
# ============================================================

class SplitProcessingFeedback(QgsProcessingFeedback):

    def __init__(self, dialog):

        super().__init__()

        self.dialog = dialog

    def isCanceled(self):

        QtWidgets.QApplication.processEvents()

        return (
            self.dialog.cancel_flag
            or super().isCanceled()
        )

    def setProgress(self, progress):

        super().setProgress(progress)

        self.dialog.progress.setValue(
            int(progress)
        )

    def setProgressText(self, text):

        super().setProgressText(text)

        self.dialog.status.setText(
            str(text)
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class UltimateSplitEngineBasic(QtWidgets.QDialog):

    def __init__(self, iface=None):

        super().__init__()

        self.iface = iface

        self.project = QgsProject.instance()

        self.layer_cache = {}

        self.cancel_flag = False

        self.running = False

        self.logo = None

        self.feedback = None

        self.setWindowTitle(
            "FjBa | Basic Ultimate Split Engine"
        )

        # Standard desktop window buttons.
        self.setWindowFlags(
            self.windowFlags()
            | WINDOW_SYSTEM_MENU
            | WINDOW_MINIMIZE
            | WINDOW_MAXIMIZE
            | WINDOW_CLOSE
        )

        self.setSizeGripEnabled(True)

        self.setMinimumSize(720, 540)

        self.resize(1080, 760)

        self.create_interface()

        self.apply_theme()

        self.connect_signals()

        self.populate_layers()

        self.adjust_to_screen()

    # ========================================================
    # ADAPTIVE WINDOW SIZE
    # ========================================================

    def adjust_to_screen(self):

        screen = self.screen()

        if screen is None:
            screen = QtWidgets.QApplication.primaryScreen()

        if screen is None:
            return

        available = screen.availableGeometry()

        # Leave room for the operating system taskbar
        # and window borders.

        target_width = min(
            1120,
            max(720, available.width() - 60)
        )

        target_height = min(
            820,
            max(540, available.height() - 70)
        )

        self.resize(
            target_width,
            target_height
        )

        self.move(
            available.center().x() - target_width // 2,
            available.center().y() - target_height // 2
        )

    # ========================================================
    # INTERFACE
    # ========================================================

    def create_interface(self):

        outer_layout = QtWidgets.QVBoxLayout(self)

        outer_layout.setContentsMargins(
            10, 10, 10, 10
        )

        outer_layout.setSpacing(0)

        # Scroll area makes the interface usable on
        # smaller laptop screens.

        self.scroll_area = QtWidgets.QScrollArea()

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setFrameShape(
            FRAME_NO_FRAME
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            SCROLLBAR_ALWAYS_OFF
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        self.content_widget = QtWidgets.QWidget()

        self.scroll_area.setWidget(
            self.content_widget
        )

        root = QtWidgets.QVBoxLayout(
            self.content_widget
        )

        root.setContentsMargins(
            12, 12, 12, 12
        )

        root.setSpacing(12)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QtWidgets.QFrame()

        header.setObjectName(
            "FjBaHeader"
        )

        header_layout = QtWidgets.QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            14, 8, 18, 8
        )

        self.logo = FjBaMetallicLogo()

        heading_layout = QtWidgets.QVBoxLayout()

        eyebrow = QtWidgets.QLabel(
            "FjBa  /  QGIS TOOLKIT"
        )

        eyebrow.setObjectName(
            "FjBaEyebrow"
        )

        heading = QtWidgets.QLabel(
            "Ultimate Split Engine"
        )

        heading.setObjectName(
            "FjBaHeading"
        )

        subtitle = QtWidgets.QLabel(
            "Line splitting and polygon attribute transfer"
        )

        subtitle.setObjectName(
            "FjBaSubtitle"
        )

        heading_layout.addWidget(eyebrow)
        heading_layout.addWidget(heading)
        heading_layout.addWidget(subtitle)

        header_layout.addWidget(
            self.logo
        )

        header_layout.addLayout(
            heading_layout,
            1
        )

        edition = QtWidgets.QLabel(
            "BASIC EDITION 1.2"
        )

        edition.setObjectName(
            "FjBaEdition"
        )

        header_layout.addWidget(
            edition
        )

        root.addWidget(header)

        # ----------------------------------------------------
        # MAIN CONTENT
        # ----------------------------------------------------

        content = QtWidgets.QHBoxLayout()

        content.setSpacing(12)

        root.addLayout(
            content,
            1
        )

        # ----------------------------------------------------
        # LEFT PANEL
        # ----------------------------------------------------

        left_panel = QtWidgets.QVBoxLayout()

        # LINE LAYERS

        line_group = QtWidgets.QGroupBox(
            "01  ·  Line layers"
        )

        line_layout = QtWidgets.QVBoxLayout(
            line_group
        )

        self.line_list = QtWidgets.QListWidget()

        self.line_list.setSelectionMode(
            MULTI_SELECTION
        )

        self.line_list.setMinimumHeight(85)

        line_layout.addWidget(
            self.line_list
        )

        left_panel.addWidget(
            line_group
        )

        # POLYGON LAYERS

        poly_group = QtWidgets.QGroupBox(
            "02  ·  Polygon layers"
        )

        poly_layout = QtWidgets.QVBoxLayout(
            poly_group
        )

        self.poly_list = QtWidgets.QListWidget()

        self.poly_list.setSelectionMode(
            MULTI_SELECTION
        )

        self.poly_list.setMinimumHeight(85)

        poly_layout.addWidget(
            self.poly_list
        )

        left_panel.addWidget(
            poly_group
        )

        # REFRESH

        self.refresh_button = QtWidgets.QPushButton(
            "↻   Refresh project layers"
        )

        left_panel.addWidget(
            self.refresh_button
        )

        # POLYGON FIELDS

        field_group = QtWidgets.QGroupBox(
            "03  ·  Polygon attributes"
        )

        field_layout = QtWidgets.QVBoxLayout(
            field_group
        )

        field_description = QtWidgets.QLabel(
            "Select the attributes to transfer to split lines."
        )

        field_description.setWordWrap(True)

        field_layout.addWidget(
            field_description
        )

        self.field_list = QtWidgets.QListWidget()

        self.field_list.setSelectionMode(
            MULTI_SELECTION
        )

        self.field_list.setMinimumHeight(100)

        field_layout.addWidget(
            self.field_list
        )

        left_panel.addWidget(
            field_group,
            1
        )

        # OUTPUT

        output_group = QtWidgets.QGroupBox(
            "04  ·  Output settings"
        )

        output_layout = QtWidgets.QFormLayout(
            output_group
        )

        self.output_name = QtWidgets.QLineEdit(
            "split_result"
        )

        output_layout.addRow(
            "Output layer name",
            self.output_name
        )

        left_panel.addWidget(
            output_group
        )

        # RUN BUTTON

        self.run_button = QtWidgets.QPushButton(
            "▶   RUN SPLIT ENGINE"
        )

        self.run_button.setObjectName(
            "FjBaPrimary"
        )

        self.run_button.setMinimumHeight(44)

        left_panel.addWidget(
            self.run_button
        )

        content.addLayout(
            left_panel,
            1
        )

        # ----------------------------------------------------
        # RIGHT PANEL
        # ----------------------------------------------------

        right_panel = QtWidgets.QVBoxLayout()

        # PROCESSING INFORMATION

        info_group = QtWidgets.QGroupBox(
            "Processing information"
        )

        info_layout = QtWidgets.QVBoxLayout(
            info_group
        )

        self.status = QtWidgets.QLabel(
            "Ready  ·  Select your input layers"
        )

        self.status.setObjectName(
            "FjBaStatus"
        )

        self.status.setWordWrap(True)

        info_layout.addWidget(
            self.status
        )

        self.progress = QtWidgets.QProgressBar()

        self.progress.setValue(0)

        self.progress.setMinimumHeight(22)

        info_layout.addWidget(
            self.progress
        )

        right_panel.addWidget(
            info_group
        )

        # PROCESSING LOG

        log_group = QtWidgets.QGroupBox(
            "Processing log"
        )

        log_layout = QtWidgets.QVBoxLayout(
            log_group
        )

        self.log_output = QtWidgets.QTextEdit()

        self.log_output.setReadOnly(True)

        self.log_output.setPlaceholderText(
            "Processing messages will appear here..."
        )

        log_layout.addWidget(
            self.log_output
        )

        right_panel.addWidget(
            log_group,
            1
        )

        # CANCEL

        self.cancel_button = QtWidgets.QPushButton(
            "■   Cancel processing"
        )

        self.cancel_button.setObjectName(
            "FjBaDanger"
        )

        self.cancel_button.setEnabled(False)

        right_panel.addWidget(
            self.cancel_button
        )

        content.addLayout(
            right_panel,
            1
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = QtWidgets.QLabel(
            "FjBa  ·  BASIC GEOSPATIAL TOOLKIT  ·  QGIS"
        )

        footer.setAlignment(
            ALIGN_CENTER
        )

        footer.setObjectName(
            "FjBaFooter"
        )

        root.addWidget(footer)

    # ========================================================
    # THEME
    # ========================================================

    def apply_theme(self):

        self.setStyleSheet("""
            QWidget {
                background: #0B1220;
                color: #E7EEF8;
                font-family: "Segoe UI", Arial;
                font-size: 10pt;
            }

            QScrollArea {
                background: #0B1220;
                border: none;
            }

            QFrame#FjBaHeader {
                background: #111F31;
                border: 1px solid #2A435B;
                border-radius: 14px;
            }

            QLabel#FjBaEyebrow {
                color: #64D6C5;
                font-weight: bold;
            }

            QLabel#FjBaHeading {
                color: #F4F8FC;
                font-size: 19pt;
                font-weight: bold;
            }

            QLabel#FjBaSubtitle {
                color: #93A8BF;
            }

            QLabel#FjBaEdition {
                color: #D5A832;
                font-weight: bold;
                border: 1px solid #806B37;
                border-radius: 7px;
                padding: 8px;
            }

            QLabel#FjBaStatus {
                background: #101D2E;
                border: 1px solid #263B52;
                border-radius: 8px;
                padding: 10px;
                color: #75DCCB;
                font-weight: bold;
            }

            QLabel#FjBaFooter {
                color: #68849B;
                font-size: 9pt;
                padding: 5px;
            }

            QGroupBox {
                background: #101B2B;
                border: 1px solid #263B52;
                border-radius: 10px;
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
                color: #78D9CD;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }

            QLineEdit {
                background: #0B1422;
                color: #F0F5FB;
                border: 1px solid #344B65;
                border-radius: 6px;
                padding: 7px;
                min-height: 20px;
            }

            QLineEdit:focus {
                border: 1px solid #55CDBD;
            }

            QListWidget {
                background: #0B1422;
                alternate-background-color: #101D2E;
                color: #E7EEF8;
                border: 1px solid #2B4058;
                border-radius: 8px;
                padding: 5px;
                selection-background-color: #175E68;
            }

            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }

            QPushButton {
                background: #173A4B;
                color: white;
                border: 1px solid #2D6874;
                border-radius: 7px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #20566A;
                border-color: #56CDBD;
            }

            QPushButton:disabled {
                background: #273444;
                color: #718096;
                border-color: #354457;
            }

            QPushButton#FjBaPrimary {
                background: #1B8B83;
                border: 1px solid #45BDB0;
            }

            QPushButton#FjBaPrimary:hover {
                background: #22A398;
            }

            QPushButton#FjBaDanger {
                background: #4A2935;
                border-color: #814454;
            }

            QTextEdit {
                background: #0B1422;
                color: #A5E6C6;
                border: 1px solid #2B4058;
                border-radius: 8px;
                padding: 8px;
                font-family: Consolas, monospace;
                font-size: 9pt;
            }

            QProgressBar {
                background: #0B1422;
                border: 1px solid #344B65;
                border-radius: 6px;
                text-align: center;
                color: white;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background: #1B9C80;
                border-radius: 5px;
            }
        """)

    # ========================================================
    # SIGNALS
    # ========================================================

    def connect_signals(self):

        self.refresh_button.clicked.connect(
            self.populate_layers
        )

        self.poly_list.itemSelectionChanged.connect(
            self.update_fields
        )

        self.run_button.clicked.connect(
            self.run
        )

        self.cancel_button.clicked.connect(
            self.cancel_run
        )

    # ========================================================
    # LOGGING
    # ========================================================

    def log(self, message, level="INFO"):

        timestamp = datetime.datetime.now().strftime(
            "%H:%M:%S"
        )

        safe_message = (
            str(message)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        self.log_output.append(
            f"[{timestamp}] {level}: {safe_message}"
        )

        print(
            f"[FjBa Split Engine] {level}: {message}"
        )

        QtWidgets.QApplication.processEvents()

    # ========================================================
    # LOAD LAYERS
    # ========================================================

    def populate_layers(self):

        if self.running:
            return

        self.line_list.clear()
        self.poly_list.clear()
        self.field_list.clear()

        self.layer_cache.clear()

        for layer in self.project.mapLayers().values():

            if layer.type() != Qgis.LayerType.Vector:
                continue

            if not layer.isValid():
                continue

            geometry_enum = getattr(QgsWkbTypes, "GeometryType", QgsWkbTypes)

            if layer.geometryType() == geometry_enum.LineGeometry:

                item = QtWidgets.QListWidgetItem(
                    layer.name()
                )

                item.setData(
                    USER_ROLE,
                    layer.id()
                )

                self.line_list.addItem(item)

            elif layer.geometryType() == geometry_enum.PolygonGeometry:

                item = QtWidgets.QListWidgetItem(
                    layer.name()
                )

                item.setData(
                    USER_ROLE,
                    layer.id()
                )

                self.poly_list.addItem(item)

            self.layer_cache[layer.id()] = layer

        self.log(
            "Project layers refreshed",
            "DONE"
        )

    # ========================================================
    # GET SELECTED LAYERS
    # ========================================================

    def selected_layers(self, widget):

        layers = []

        for item in widget.selectedItems():

            layer_id = item.data(
                USER_ROLE
            )

            layer = self.project.mapLayer(
                layer_id
            )

            if layer and layer.isValid():
                layers.append(layer)

        return layers

    # ========================================================
    # UPDATE POLYGON FIELDS
    # ========================================================

    def update_fields(self):

        self.field_list.clear()

        for layer in self.selected_layers(
            self.poly_list
        ):

            for field in layer.fields():

                item = QtWidgets.QListWidgetItem(
                    f"{layer.name()}  ::  {field.name()}"
                )

                item.setData(
                    USER_ROLE,
                    (layer.id(), field.name())
                )

                self.field_list.addItem(item)

    # ========================================================
    # GET SELECTED FIELDS
    # ========================================================

    def selected_fields(self):

        result = []

        for item in self.field_list.selectedItems():

            data = item.data(USER_ROLE)

            if data:
                result.append(data)

        return result

    # ========================================================
    # CHECK INPUT CRS
    # ========================================================

    def validate_crs(self, line_layers, poly_layers):

        all_layers = line_layers + poly_layers

        if not line_layers:
            raise ValueError("No line layers selected.")

        if not poly_layers:
            raise ValueError("No polygon layers selected.")

        reference_crs = line_layers[0].crs()

        if not reference_crs.isValid():
            raise ValueError("The line layer CRS is invalid.")

        for layer in all_layers:

            if not layer.crs().isValid():
                raise ValueError(
                    f"Layer '{layer.name()}' has an invalid CRS."
                )

            if layer.crs() != reference_crs:

                raise ValueError(
                    "All selected line and polygon layers must use "
                    "the same CRS. Reproject your layers before processing."
                )

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel_run(self):

        if not self.running:
            return

        self.cancel_flag = True

        self.status.setText(
            "Cancellation requested..."
        )

        self.log(
            "Cancellation requested",
            "WARNING"
        )

    # ========================================================
    # PROCESSING HELPER
    # ========================================================

    def run_algorithm(self, algorithm, parameters):

        if self.cancel_flag:
            raise InterruptedError(
                "Processing cancelled."
            )

        return processing.run(
            algorithm,
            parameters,
            feedback=self.feedback
        )

    # ========================================================
    # MAIN PROCESSING
    # ========================================================

    def run(self):

        if self.running:
            return

        self.cancel_flag = False
        self.running = True

        self.progress.setValue(0)

        self.run_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        output_name = self.output_name.text().strip()

        try:

            if not output_name:
                raise ValueError(
                    "Enter an output layer name."
                )

            line_layers = self.selected_layers(
                self.line_list
            )

            poly_layers = self.selected_layers(
                self.poly_list
            )

            selected_fields = self.selected_fields()

            self.validate_crs(
                line_layers,
                poly_layers
            )

            self.feedback = SplitProcessingFeedback(
                self
            )

            self.log(
                "Starting Ultimate Split Engine",
                "START"
            )

            # ------------------------------------------------
            # 01. FIX POLYGONS
            # ------------------------------------------------

            self.status.setText(
                "01/06  ·  Fixing polygon geometries..."
            )

            self.progress.setValue(5)

            fixed_polys = {}

            for i, layer in enumerate(poly_layers):

                if self.cancel_flag:
                    raise InterruptedError(
                        "Processing cancelled."
                    )

                self.log(
                    f"Fixing: {layer.name()}"
                )

                result = self.run_algorithm(
                    "native:fixgeometries",
                    {
                        "INPUT": layer,
                        "OUTPUT": "memory:"
                    }
                )

                fixed_polys[layer.id()] = result["OUTPUT"]

                self.progress.setValue(
                    5 + int(
                        15 * (i + 1) / len(poly_layers)
                    )
                )

            # ------------------------------------------------
            # 02. MERGE LINE LAYERS
            # ------------------------------------------------

            self.status.setText(
                "02/06  ·  Merging line layers..."
            )

            self.progress.setValue(22)

            merged_lines = self.run_algorithm(
                "native:mergevectorlayers",
                {
                    "LAYERS": line_layers,
                    "CRS": line_layers[0].crs(),
                    "OUTPUT": "memory:"
                }
            )["OUTPUT"]

            merged_lines = self.run_algorithm(
                "native:multiparttosingleparts",
                {
                    "INPUT": merged_lines,
                    "OUTPUT": "memory:"
                }
            )["OUTPUT"]

            # ------------------------------------------------
            # 03. EXTRACT POLYGON BOUNDARIES
            # ------------------------------------------------

            self.status.setText(
                "03/06  ·  Extracting polygon boundaries..."
            )

            self.progress.setValue(32)

            boundary_layers = []

            for layer_id, fixed_layer in fixed_polys.items():

                boundary = self.run_algorithm(
                    "native:polygonstolines",
                    {
                        "INPUT": fixed_layer,
                        "OUTPUT": "memory:"
                    }
                )["OUTPUT"]

                boundary_layers.append(boundary)

            merged_boundaries = self.run_algorithm(
                "native:mergevectorlayers",
                {
                    "LAYERS": boundary_layers,
                    "CRS": line_layers[0].crs(),
                    "OUTPUT": "memory:"
                }
            )["OUTPUT"]

            # ------------------------------------------------
            # 04. SPLIT LINES
            # ------------------------------------------------

            self.status.setText(
                "04/06  ·  Splitting lines..."
            )

            self.progress.setValue(40)

            split_lines = self.run_algorithm(
                "native:splitwithlines",
                {
                    "INPUT": merged_lines,
                    "LINES": merged_boundaries,
                    "OUTPUT": "memory:"
                }
            )["OUTPUT"]

            split_lines = self.run_algorithm(
                "native:multiparttosingleparts",
                {
                    "INPUT": split_lines,
                    "OUTPUT": "memory:"
                }
            )["OUTPUT"]

            total = split_lines.featureCount()

            if total == 0:
                raise ValueError(
                    "No output line segments were created."
                )

            self.log(
                f"Created {total} line segments"
            )

            # ------------------------------------------------
            # 05. BUILD SPATIAL INDEXES
            # ------------------------------------------------

            self.status.setText(
                "05/06  ·  Building spatial indexes..."
            )

            self.progress.setValue(50)

            polygon_data = {}

            for layer_id, fixed_layer in fixed_polys.items():

                poly_features = list(
                    fixed_layer.getFeatures()
                )

                index = QgsSpatialIndex()

                index.addFeatures(
                    poly_features
                )

                feature_dict = {
                    feature.id(): feature
                    for feature in poly_features
                }

                polygon_data[layer_id] = {
                    "index": index,
                    "features": feature_dict,
                    "layer": fixed_layer
                }

            # ------------------------------------------------
            # 06. CREATE OUTPUT FIELDS
            # ------------------------------------------------

            self.status.setText(
                "06/06  ·  Preparing output..."
            )

            output_geometry_name = QgsWkbTypes.displayString(
                split_lines.wkbType()
            )

            if not output_geometry_name or output_geometry_name == "Unknown":
                raise RuntimeError(
                    "The split result has an unsupported geometry type."
                )

            out = QgsVectorLayer(
                output_geometry_name,
                output_name,
                "memory"
            )
            out.setCrs(split_lines.crs())

            if not out.isValid():
                raise RuntimeError(
                    "Could not create output layer."
                )

            provider = out.dataProvider()

            output_fields = QgsFields()

            for field in split_lines.fields():
                output_fields.append(
                    QgsField(field)
                )

            field_mapping = []

            used_names = {
                field.name().lower()
                for field in output_fields
            }

            for layer_id, field_name in selected_fields:

                layer = self.project.mapLayer(layer_id)

                if layer is None:
                    continue

                fixed_layer = fixed_polys[layer_id]

                source_index = (
                    fixed_layer.fields().indexOf(
                        field_name
                    )
                )

                if source_index < 0:
                    continue

                source_field = fixed_layer.fields()[
                    source_index
                ]

                prefix = re.sub(
                    r"[^A-Za-z0-9_]",
                    "_",
                    layer.name()
                )

                base_name = (
                    f"{prefix}_{field_name}"
                )

                output_field_name = base_name

                counter = 2

                while output_field_name.lower() in used_names:

                    output_field_name = (
                        f"{base_name}_{counter}"
                    )

                    counter += 1

                used_names.add(
                    output_field_name.lower()
                )

                new_field = QgsField(
                    source_field
                )

                new_field.setName(
                    output_field_name
                )

                output_fields.append(
                    new_field
                )

                field_mapping.append({
                    "layer_id": layer_id,
                    "field_name": field_name,
                    "field_index": source_index,
                    "output_name": output_field_name
                })

            if not provider.addAttributes(list(output_fields)):
                raise RuntimeError("Could not create the output attribute fields.")

            out.updateFields()

            # ------------------------------------------------
            # ATTRIBUTE TRANSFER
            # ------------------------------------------------

            self.status.setText(
                "Assigning polygon attributes..."
            )

            self.progress.setValue(55)

            new_features = []

            processed_count = 0
            mapped_layer_ids = {
                mapping["layer_id"] for mapping in field_mapping
            }

            for i, feat in enumerate(
                split_lines.getFeatures()
            ):

                if self.cancel_flag:
                    raise InterruptedError(
                        "Processing cancelled."
                    )

                if not feat.hasGeometry():
                    continue

                geom = feat.geometry()

                if geom.isEmpty():
                    continue

                attrs = feat.attributes()

                # Determine the winning polygon once per source polygon layer.
                # All selected attributes from that layer are then read from the
                # same winning feature, avoiding repeated GEOS intersections.
                best_polygon_by_layer = {}

                for layer_id, data in polygon_data.items():

                    if layer_id not in mapped_layer_ids:
                        continue

                    if self.cancel_flag:
                        raise InterruptedError("Processing cancelled.")

                    candidates = sorted(
                        data["index"].intersects(geom.boundingBox())
                    )

                    best_polygon = None
                    best_score = 0.0

                    for polygon_id in candidates:

                        if self.cancel_flag:
                            raise InterruptedError("Processing cancelled.")

                        polygon_feature = data["features"].get(polygon_id)
                        if polygon_feature is None or not polygon_feature.hasGeometry():
                            continue

                        polygon_geometry = polygon_feature.geometry()
                        if polygon_geometry.isNull() or polygon_geometry.isEmpty():
                            continue

                        if not polygon_geometry.intersects(geom):
                            continue

                        intersection = geom.intersection(polygon_geometry)
                        if intersection.isNull() or intersection.isEmpty():
                            continue

                        score = intersection.length()

                        # Stable tie behavior: sorted feature IDs mean the first
                        # feature wins when intersection lengths are equal.
                        if score > best_score:
                            best_score = score
                            best_polygon = polygon_feature

                    best_polygon_by_layer[layer_id] = best_polygon

                new_values = []

                for mapping in field_mapping:

                    winning_polygon = best_polygon_by_layer.get(
                        mapping["layer_id"]
                    )

                    if winning_polygon is None:
                        new_values.append(None)
                    else:
                        new_values.append(
                            winning_polygon.attribute(mapping["field_index"])
                        )

                new_feat = QgsFeature(
                    out.fields()
                )

                new_feat.setGeometry(
                    QgsGeometry(geom)
                )

                new_feat.setAttributes(
                    attrs + new_values
                )

                new_features.append(
                    new_feat
                )

                processed_count += 1

                self.progress.setValue(
                    55 + int(
                        40 * (i + 1) / max(1, total)
                    )
                )

                if i % 100 == 0:

                    self.status.setText(
                        f"Assigning attributes {i + 1}/{total}"
                    )

                    QtWidgets.QApplication.processEvents()

            # ------------------------------------------------
            # ADD FEATURES
            # ------------------------------------------------

            if self.cancel_flag:
                raise InterruptedError(
                    "Processing cancelled."
                )

            success, added_features = provider.addFeatures(
                new_features
            )

            if not success:
                raise RuntimeError(
                    "Could not write all output features."
                )

            out.updateExtents()

            # ------------------------------------------------
            # ADD TO QGIS PROJECT
            # ------------------------------------------------

            self.project.addMapLayer(out)

            self.progress.setValue(100)

            self.status.setText(
                "Completed successfully"
            )

            self.log(
                f"Output: {output_name}",
                "DONE"
            )

            self.log(
                f"Output features: {processed_count}",
                "DONE"
            )

            self.log(
                f"Transferred fields: {len(field_mapping)}",
                "DONE"
            )

            QtWidgets.QMessageBox.information(
                self,
                "FjBa Basic Split Engine",
                "Processing completed successfully!\n\n"
                f"Output layer: {output_name}\n"
                f"Features: {processed_count}\n"
                f"Transferred fields: {len(field_mapping)}"
            )

        except InterruptedError as error:

            self.status.setText(
                "Processing cancelled"
            )

            self.log(
                str(error),
                "WARNING"
            )

        except Exception as error:

            self.status.setText(
                "Processing failed"
            )

            self.log(
                str(error),
                "ERROR"
            )

            self.log(
                traceback.format_exc(),
                "TRACEBACK"
            )

            QtWidgets.QMessageBox.critical(
                self,
                "FjBa Split Engine Error",
                str(error)
            )

        finally:

            self.running = False

            self.feedback = None

            self.run_button.setEnabled(True)

            self.refresh_button.setEnabled(True)

            self.cancel_button.setEnabled(False)

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(self, event):

        if self.running:

            answer = QtWidgets.QMessageBox.question(
                self,
                "Processing active",
                "Processing is still active. Request cancellation?",
                MESSAGE_YES
                | MESSAGE_NO,
                MESSAGE_NO
            )

            if answer != MESSAGE_YES:
                event.ignore()
                return

            self.cancel_flag = True

            # Keep the dialog alive until synchronous
            # processing has returned safely.

            event.ignore()
            return

        if self.logo is not None:

            self.logo.stop()

            self.logo = None

        event.accept()


# ============================================================
# QGIS ENTRY POINT
# ============================================================

_fjba_split_window = None


def main(iface):

    global _fjba_split_window

    try:

        if (
            _fjba_split_window is not None
            and _fjba_split_window.isVisible()
        ):

            _fjba_split_window.raise_()

            _fjba_split_window.activateWindow()

            return _fjba_split_window

        _fjba_split_window = UltimateSplitEngineBasic(
            iface
        )

        _fjba_split_window.show()

        _fjba_split_window.raise_()

        _fjba_split_window.activateWindow()

        return _fjba_split_window

    except Exception:

        QtWidgets.QMessageBox.critical(
            iface.mainWindow(),
            "FjBa Basic Split Engine Error",
            traceback.format_exc()
        )

        return None


# ============================================================
# END OF FjBa BASIC ULTIMATE SPLIT ENGINE 1.2
# ============================================================
