
# -*- coding: utf-8 -*-
"""
==========================================================================
FjBa Plugin Generator V8.3 PRO
QGIS Plugin Main Module
==========================================================================

Features:
    - Qt5 / Qt6 compatibility
    - Safe plugin initialization and unloading
    - Correct QAction ownership
    - Automatic FjBa branding for supported windows
    - Dynamic script.py loading
    - Safe window management
    - Plugin reload support
    - Error logging and diagnostic messages

IMPORTANT:
    FjBaBrandingManager does NOT own the plugin QAction.
    Only FjBaGeneratedPlugin manages self.action.
==========================================================================
"""

import os
import sys
import inspect
import traceback
import weakref
import importlib.util
import builtins

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtCore import Qt, QObject, QEvent
from qgis.PyQt.QtGui import QIcon, QPixmap

# QAction moved from QtWidgets to QtGui in Qt6.
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction

from qgis.PyQt.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
)


# ============================================================
# PLUGIN CONFIGURATION
# ============================================================

PLUGIN_DISPLAY_NAME = (
    "FjBa_Basic_Split_Line_Take_Polyinformation"
)

PLUGIN_MENU_NAME = "&FjBa Generated Plugins"

SCRIPT_MODULE_SUFFIX = "._fjba_user_script"


# ============================================================
# QT5 / QT6 COMPATIBILITY
# ============================================================

def enum_value(owner, group_name, member_name):
    """
    Resolve Qt5 and Qt6 enum members.

    Qt6 groups many enums into nested classes.
    Qt5 commonly exposes the members directly.
    """

    group = getattr(owner, group_name, owner)

    return getattr(group, member_name)


ALIGN_CENTER = enum_value(
    Qt,
    "AlignmentFlag",
    "AlignCenter"
)

WA_TRANSPARENT = enum_value(
    Qt,
    "WidgetAttribute",
    "WA_TransparentForMouseEvents"
)

WA_NO_BACKGROUND = enum_value(
    Qt,
    "WidgetAttribute",
    "WA_NoSystemBackground"
)

KEEP_ASPECT = enum_value(
    Qt,
    "AspectRatioMode",
    "KeepAspectRatio"
)

SMOOTH_TRANSFORM = enum_value(
    Qt,
    "TransformationMode",
    "SmoothTransformation"
)

EVENT_SHOW = enum_value(
    QEvent,
    "Type",
    "Show"
)

EVENT_RESIZE = enum_value(
    QEvent,
    "Type",
    "Resize"
)

EVENT_MOVE = enum_value(
    QEvent,
    "Type",
    "Move"
)

EVENT_WINDOW_STATE = enum_value(
    QEvent,
    "Type",
    "WindowStateChange"
)

EVENT_CLOSE = enum_value(
    QEvent,
    "Type",
    "Close"
)

WINDOW_MINIMIZE = enum_value(
    Qt,
    "WindowType",
    "WindowMinimizeButtonHint"
)

WINDOW_MAXIMIZE = enum_value(
    Qt,
    "WindowType",
    "WindowMaximizeButtonHint"
)

WINDOW_CLOSE = enum_value(
    Qt,
    "WindowType",
    "WindowCloseButtonHint"
)


# ============================================================
# LOGGING
# ============================================================

def log_message(message, level=None):
    """
    Write a message to the QGIS log.
    Falls back to stderr if QGIS logging is unavailable.
    """

    if level is None:
        level = Qgis.MessageLevel.Warning

    try:
        QgsMessageLog.logMessage(
            str(message),
            PLUGIN_DISPLAY_NAME,
            level
        )

    except Exception as error:
        sys.stderr.write(
            "[FjBa Plugin] QGIS logging failed: {}\n".format(error)
        )

        sys.stderr.write(
            "[FjBa Plugin] {}\n".format(message)
        )


def log_exception(context):
    """Write the current exception traceback to the QGIS log."""

    message = "{}\n{}".format(
        context,
        traceback.format_exc()
    )

    log_message(message)


def safe_close(widget):
    """Safely close a Qt widget."""

    if widget is None:
        return

    try:
        widget.close()

    except RuntimeError:
        pass

    except Exception:
        log_exception("Error while closing plugin window")


# ============================================================
# BRANDING MANAGER
# ============================================================

class FjBaBrandingManager(QObject):
    """
    Manages FjBa logo overlays on supported plugin windows.

    This class does NOT own:
        - QAction
        - Plugin menu entries
        - Toolbar entries

    Its unload() method only removes branding resources
    and event filters.
    """

    def __init__(self, iface, logo_path):

        super().__init__()

        self.iface = iface
        self.logo_path = logo_path

        self.application = QApplication.instance()

        self.active = False
        self.windows = {}

        self.logo = QPixmap(logo_path)

        self._unloaded = False

        if self.application is not None:

            self.application.installEventFilter(self)

    # --------------------------------------------------------
    # CAPTURE CONTROL
    # --------------------------------------------------------

    def start_capture(self):

        if self._unloaded:
            return

        self.active = True

    def stop_capture(self):

        self.active = False

    # --------------------------------------------------------
    # WINDOW VALIDATION
    # --------------------------------------------------------

    def _is_supported_window(self, widget):

        if not isinstance(widget, QWidget):
            return False

        try:

            if not widget.isWindow():
                return False

            if self.iface is not None:

                main_window = self.iface.mainWindow()

                if widget is main_window:
                    return False

        except RuntimeError:
            return False

        except Exception:
            return False

        return True

    # --------------------------------------------------------
    # APPLICATION EVENT FILTER
    # --------------------------------------------------------

    def eventFilter(self, watched, event):

        if self._unloaded:
            return False

        try:

            event_type = event.type()

            if event_type == EVENT_SHOW:

                if (
                    self.active
                    and isinstance(watched, QWidget)
                ):

                    self.register_window(watched)

            elif event_type in (
                EVENT_RESIZE,
                EVENT_MOVE,
                EVENT_WINDOW_STATE
            ):

                if isinstance(watched, QWidget):

                    self._position_logo(watched)

            elif event_type == EVENT_CLOSE:

                if isinstance(watched, QWidget):

                    self._remove_window(watched)

        except RuntimeError:
            pass

        except Exception:
            log_exception("Branding event filter error")

        return False

    # --------------------------------------------------------
    # REGISTER WINDOW
    # --------------------------------------------------------

    def register_window(self, widget):

        if self._unloaded:
            return

        if not self._is_supported_window(widget):
            return

        key = id(widget)

        if key in self.windows:

            self._position_logo(widget)

            return

        if self.logo.isNull():
            return

        try:

            widget.setWindowIcon(
                QIcon(self.logo_path)
            )

            label = QLabel(widget)

            label.setObjectName(
                "fjbaBrandOverlay"
            )

            label.setAttribute(
                WA_TRANSPARENT,
                True
            )

            label.setAttribute(
                WA_NO_BACKGROUND,
                True
            )

            label.setAlignment(
                ALIGN_CENTER
            )

            scaled = self.logo.scaled(
                112,
                48,
                KEEP_ASPECT,
                SMOOTH_TRANSFORM
            )

            label.setPixmap(scaled)

            label.resize(
                scaled.size()
            )

            self.windows[key] = {
                "window": weakref.ref(widget),
                "label": label,
            }

            widget.installEventFilter(self)

            label.show()
            label.raise_()

            self._position_logo(widget)

        except RuntimeError as error:

            log_message(
                "Could not brand window: {}".format(error)
            )

        except Exception:

            log_exception(
                "Unexpected error while branding window"
            )

    # --------------------------------------------------------
    # POSITION LOGO
    # --------------------------------------------------------

    def _position_logo(self, widget):

        if self._unloaded:
            return

        record = self.windows.get(id(widget))

        if record is None:
            return

        try:

            label = record.get("label")

            if label is None:
                return

            margin = 12

            x = max(
                margin,
                widget.width() - label.width() - margin
            )

            y = margin

            label.move(x, y)

            label.raise_()

        except RuntimeError:

            self._remove_window(widget)

        except Exception:

            log_exception(
                "Could not reposition branding logo"
            )

    # --------------------------------------------------------
    # REMOVE SINGLE WINDOW
    # --------------------------------------------------------

    def _remove_window(self, widget):

        if widget is None:
            return

        record = self.windows.pop(
            id(widget),
            None
        )

        if record is None:
            return

        label = record.get("label")

        if label is not None:

            try:
                label.deleteLater()

            except RuntimeError:
                pass

        try:

            widget.removeEventFilter(self)

        except (RuntimeError, AttributeError):
            pass

    # --------------------------------------------------------
    # BRAND EXISTING WINDOW
    # --------------------------------------------------------

    def brand_existing(self, widget):

        if self._unloaded:
            return

        if isinstance(widget, QWidget):

            self.register_window(widget)

    # --------------------------------------------------------
    # UNLOAD BRANDING MANAGER
    # --------------------------------------------------------

    def unload(self):
        """
        Release branding resources.

        IMPORTANT:
        This method must NEVER access self.action.
        QAction belongs exclusively to FjBaGeneratedPlugin.
        """

        if self._unloaded:
            return

        self._unloaded = True

        self.active = False

        for key, record in list(self.windows.items()):

            widget_ref = record.get("window")

            widget = (
                widget_ref()
                if widget_ref is not None
                else None
            )

            label = record.get("label")

            if label is not None:

                try:
                    label.deleteLater()

                except RuntimeError:
                    pass

            if widget is not None:

                try:

                    widget.removeEventFilter(self)

                except (RuntimeError, AttributeError):
                    pass

        self.windows.clear()

        if self.application is not None:

            try:

                self.application.removeEventFilter(
                    self
                )

            except RuntimeError:
                pass

        self.application = None
        self.iface = None
        self.logo = QPixmap()


# ============================================================
# GENERATED PLUGIN
# ============================================================

class FjBaGeneratedPlugin:
    """
    Main QGIS plugin controller.

    This class owns:
        - QAction
        - QGIS menu registration
        - QGIS toolbar registration
        - Launcher window
        - Script window references
        - About dialog
        - Dynamic script module
        - Branding manager lifecycle
    """

    def __init__(self, iface):

        self.iface = iface

        # QAction ownership belongs here.
        self.action = None

        # Plugin windows.
        self.launch_window = None
        self.script_window = None
        self.about_dialog = None

        # Plugin directory.
        self.plugin_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        # Image assets.
        self.logo_path = os.path.join(
            self.plugin_dir,
            "fjba_logo.png"
        )

        self.icon_path = os.path.join(
            self.plugin_dir,
            "icon.png"
        )

        # Dynamic script state.
        self._script_module = None
        self._script_loaded = False
        self._script_running = False

        # Lifecycle state.
        self._unloaded = False

        # Branding manager.
        self.branding = FjBaBrandingManager(
            iface,
            self.logo_path
        )

    # ========================================================
    # ACTION ICON
    # ========================================================

    def _plugin_action_icon(self):

        if os.path.isfile(self.icon_path):

            return QIcon(
                self.icon_path
            )

        return QIcon()

    # ========================================================
    # INITIALIZE GUI
    # ========================================================

    def initGui(self):
        """Register plugin action in QGIS."""

        if self._unloaded:
            return

        if self.action is not None:
            return

        try:

            self.action = QAction(
                self._plugin_action_icon(),
                "Open " + PLUGIN_DISPLAY_NAME,
                self.iface.mainWindow()
            )

            self.action.triggered.connect(
                self.run
            )

            self.iface.addPluginToMenu(
                PLUGIN_MENU_NAME,
                self.action
            )

            self.iface.addToolBarIcon(
                self.action
            )

            log_message(
                "Plugin GUI initialized successfully."
            )

        except Exception:

            log_exception(
                "Could not initialize plugin GUI"
            )

            # Clean up a partially registered action.
            self._remove_action()

            raise

    # ========================================================
    # REMOVE ACTION
    # ========================================================

    def _remove_action(self):
        """
        Remove the QAction from QGIS.

        This method belongs to FjBaGeneratedPlugin only.
        """

        if self.action is None:
            return

        action = self.action

        # Clear the reference first to avoid duplicate cleanup.
        self.action = None

        try:

            action.triggered.disconnect(
                self.run
            )

        except (RuntimeError, TypeError):
            pass

        try:

            self.iface.removePluginMenu(
                PLUGIN_MENU_NAME,
                action
            )

        except (RuntimeError, AttributeError):
            pass

        except Exception:

            log_exception(
                "Could not remove plugin menu action"
            )

        try:

            self.iface.removeToolBarIcon(
                action
            )

        except (RuntimeError, AttributeError):
            pass

        except Exception:

            log_exception(
                "Could not remove toolbar action"
            )

        try:

            action.deleteLater()

        except RuntimeError:
            pass

    # ========================================================
    # DYNAMIC SCRIPT MODULE CLEANUP
    # ========================================================

    def _remove_script_module(self):
        """
        Remove the dynamically loaded script module.

        Prevents an old module reference from remaining
        in sys.modules after plugin unloading.
        """

        module_name = (
            self.__class__.__module__
            + SCRIPT_MODULE_SUFFIX
        )

        try:

            sys.modules.pop(
                module_name,
                None
            )

        except Exception:

            log_exception(
                "Could not remove dynamic script module"
            )

        self._script_module = None
        self._script_loaded = False

    # ========================================================
    # UNLOAD PLUGIN
    # ========================================================

    def unload(self):
        """
        Safely unload the plugin.

        Correct ownership:
            - self.action belongs to this class.
            - self.branding.unload() manages branding only.
        """

        if self._unloaded:
            return

        self._unloaded = True

        log_message(
            "Starting plugin unload."
        )

        # ----------------------------------------------------
        # 1. Remove QGIS QAction, menu and toolbar entry.
        # ----------------------------------------------------

        self._remove_action()

        # ----------------------------------------------------
        # 2. Stop branding manager.
        # ----------------------------------------------------

        if self.branding is not None:

            branding = self.branding

            self.branding = None

            try:

                branding.unload()

            except Exception:

                log_exception(
                    "Could not unload branding manager"
                )

        # ----------------------------------------------------
        # 3. Close plugin-owned windows.
        # ----------------------------------------------------

        for name in (
            "about_dialog",
            "script_window",
            "launch_window"
        ):

            widget = getattr(
                self,
                name,
                None
            )

            if widget is not None:

                safe_close(widget)

                setattr(
                    self,
                    name,
                    None
                )

        # ----------------------------------------------------
        # 4. Remove dynamically loaded module.
        # ----------------------------------------------------

        self._remove_script_module()

        self._script_running = False

        log_message(
            "Plugin unloaded successfully."
        )

    # ========================================================
    # MAIN LAUNCHER WINDOW
    # ========================================================

    def run(self):
        """Open the main plugin launcher."""

        if self._unloaded:
            return

        if self.launch_window is not None:

            try:

                self.launch_window.show()
                self.launch_window.raise_()
                self.launch_window.activateWindow()

                return

            except RuntimeError:

                self.launch_window = None

        try:

            window = QDialog(
                self.iface.mainWindow()
            )

            window.setWindowTitle(
                PLUGIN_DISPLAY_NAME
            )

            window.setMinimumSize(
                480,
                450
            )

            window.resize(
                540,
                520
            )

            window.setWindowIcon(
                QIcon(self.logo_path)
            )

            window.setWindowFlags(
                window.windowFlags()
                | WINDOW_MINIMIZE
                | WINDOW_MAXIMIZE
                | WINDOW_CLOSE
            )

            window.setStyleSheet("""
                QDialog {
                    background-color: #101b24;
                    color: #e8f0ed;
                }

                QLabel {
                    color: #e8f0ed;
                }

                QLabel#title {
                    color: #70d6a3;
                    font-size: 21pt;
                    font-weight: bold;
                }

                QLabel#subtitle {
                    color: #9aada8;
                    font-size: 10pt;
                }

                QPushButton {
                    background-color: #243a42;
                    color: #e8f0ed;
                    border: 1px solid #41645a;
                    border-radius: 7px;
                    padding: 11px 18px;
                    min-height: 22px;
                    font-size: 10pt;
                }

                QPushButton:hover {
                    background-color: #31534b;
                    border-color: #70d6a3;
                }

                QPushButton#openButton {
                    background-color: #267a59;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #56b88b;
                }

                QPushButton#openButton:hover {
                    background-color: #32976e;
                }
            """)

            layout = QVBoxLayout(
                window
            )

            layout.setContentsMargins(
                28,
                24,
                28,
                24
            )

            layout.setSpacing(13)

            # Logo.
            logo_label = QLabel()

            logo_label.setAlignment(
                ALIGN_CENTER
            )

            logo_label.setMinimumHeight(
                145
            )

            pixmap = QPixmap(
                self.logo_path
            )

            if not pixmap.isNull():

                logo_label.setPixmap(
                    pixmap.scaled(
                        340,
                        135,
                        KEEP_ASPECT,
                        SMOOTH_TRANSFORM
                    )
                )

            layout.addWidget(
                logo_label
            )

            # Title.
            title = QLabel(
                PLUGIN_DISPLAY_NAME
            )

            title.setObjectName(
                "title"
            )

            title.setAlignment(
                ALIGN_CENTER
            )

            title.setWordWrap(
                True
            )

            layout.addWidget(
                title
            )

            # Subtitle.
            subtitle = QLabel(
                "Powered by FjBa Plugin Generator V8.3 PRO"
            )

            subtitle.setObjectName(
                "subtitle"
            )

            subtitle.setAlignment(
                ALIGN_CENTER
            )

            subtitle.setWordWrap(
                True
            )

            layout.addWidget(
                subtitle
            )

            # Open button.
            open_button = QPushButton(
                "Open Plugin"
            )

            open_button.setObjectName(
                "openButton"
            )

            open_button.clicked.connect(
                self.open_generated_script
            )

            layout.addWidget(
                open_button
            )

            # About button.
            about_button = QPushButton(
                "About FjBa"
            )

            about_button.clicked.connect(
                self.show_about
            )

            layout.addWidget(
                about_button
            )

            # Close button.
            close_button = QPushButton(
                "Close"
            )

            close_button.clicked.connect(
                window.close
            )

            layout.addWidget(
                close_button
            )

            self.launch_window = window

            if self.branding is not None:

                self.branding.brand_existing(
                    window
                )

            window.show()
            window.raise_()
            window.activateWindow()

        except Exception:

            log_exception(
                "Could not open plugin launcher"
            )

            QMessageBox.critical(
                self.iface.mainWindow(),
                "FjBa Plugin Error",
                "The plugin launcher could not be opened.\n\n"
                + traceback.format_exc()
            )

    # ========================================================
    # LOAD GENERATED SCRIPT
    # ========================================================

    def _load_script_module(self):
        """
        Load script.py dynamically.

        The builtins.iface compatibility reference is
        temporary and is restored after module loading.
        """

        if self._unloaded:

            raise RuntimeError(
                "The plugin has already been unloaded."
            )

        if self._script_loaded:

            return self._script_module

        script_path = os.path.join(
            self.plugin_dir,
            "script.py"
        )

        if not os.path.isfile(script_path):

            raise FileNotFoundError(
                "Generated script.py was not found:\n"
                + script_path
            )

        module_name = (
            self.__class__.__module__
            + SCRIPT_MODULE_SUFFIX
        )

        had_iface = hasattr(
            builtins,
            "iface"
        )

        previous_iface = getattr(
            builtins,
            "iface",
            None
        )

        builtins.iface = self.iface

        try:

            spec = importlib.util.spec_from_file_location(
                module_name,
                script_path
            )

            if (
                spec is None
                or spec.loader is None
            ):

                raise ImportError(
                    "Could not create a module loader "
                    "for script.py."
                )

            module = importlib.util.module_from_spec(
                spec
            )

            sys.modules[module_name] = module

            try:

                spec.loader.exec_module(
                    module
                )

            except Exception:

                sys.modules.pop(
                    module_name,
                    None
                )

                raise

            self._script_module = module
            self._script_loaded = True

            log_message(
                "Generated script.py loaded successfully."
            )

            return module

        finally:

            if had_iface:

                builtins.iface = previous_iface

            else:

                try:

                    del builtins.iface

                except AttributeError:
                    pass

    # ========================================================
    # DETERMINE MAIN FUNCTION ARGUMENTS
    # ========================================================

    @staticmethod
    def _main_requires_iface(entry):
        """
        Determine whether main() accepts an iface argument.

        Supports:
            def main()
            def main(iface)
            def main(*args)
        """

        try:

            signature = inspect.signature(
                entry
            )

        except (ValueError, TypeError):

            # Conservative fallback.
            return True

        parameters = list(
            signature.parameters.values()
        )

        positional = [

            parameter

            for parameter in parameters

            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD
            )

        ]

        has_varargs = any(

            parameter.kind == inspect.Parameter.VAR_POSITIONAL

            for parameter in parameters

        )

        return bool(
            positional or has_varargs
        )

    # ========================================================
    # OPEN GENERATED SCRIPT
    # ========================================================

    def open_generated_script(self):
        """Execute the generated script.py main() function."""

        if self._script_running or self._unloaded:
            return

        self._script_running = True

        try:

            script_module = self._load_script_module()

            entry = getattr(
                script_module,
                "main",
                None
            )

            if not callable(entry):

                QMessageBox.warning(
                    self.launch_window,
                    "FjBa Plugin",
                    "The generated script does not contain "
                    "a callable main() function."
                )

                return

            needs_iface = self._main_requires_iface(
                entry
            )

            if self.branding is not None:

                self.branding.start_capture()

            try:

                if needs_iface:

                    result = entry(
                        self.iface
                    )

                else:

                    result = entry()

            finally:

                if self.branding is not None:

                    self.branding.stop_capture()

            if isinstance(result, QWidget):

                self.script_window = result

                if self.branding is not None:

                    self.branding.brand_existing(
                        result
                    )

                result.show()
                result.raise_()
                result.activateWindow()

            log_message(
                "Generated script started successfully."
            )

        except Exception as error:

            if self.branding is not None:

                self.branding.stop_capture()

            log_exception(
                "Generated script execution failed"
            )

            QMessageBox.critical(
                self.launch_window,
                "FjBa Plugin Error",
                "The generated script could not be started:\n\n"
                + str(error)
                + "\n\nTechnical details:\n"
                + traceback.format_exc()
            )

        finally:

            self._script_running = False

    # ========================================================
    # ABOUT WINDOW
    # ========================================================

    def show_about(self):
        """Display plugin information."""

        if self._unloaded:
            return

        if self.about_dialog is not None:

            try:

                self.about_dialog.show()
                self.about_dialog.raise_()
                self.about_dialog.activateWindow()

                return

            except RuntimeError:

                self.about_dialog = None

        try:

            dialog = QDialog(
                self.launch_window
            )

            dialog.setWindowTitle(
                "About FjBa"
            )

            dialog.setMinimumWidth(
                390
            )

            dialog.setWindowIcon(
                QIcon(self.logo_path)
            )

            dialog.setStyleSheet("""
                QDialog {
                    background-color: #101b24;
                    color: #e8f0ed;
                }

                QLabel {
                    color: #e8f0ed;
                    font-size: 10pt;
                }

                QPushButton {
                    background-color: #267a59;
                    color: white;
                    border: 1px solid #56b88b;
                    border-radius: 6px;
                    padding: 8px 18px;
                }

                QPushButton:hover {
                    background-color: #32976e;
                }
            """)

            layout = QVBoxLayout(
                dialog
            )

            layout.setContentsMargins(
                22,
                22,
                22,
                22
            )

            layout.setSpacing(
                14
            )

            # Logo.
            pixmap = QPixmap(
                self.logo_path
            )

            if not pixmap.isNull():

                logo = QLabel()

                logo.setAlignment(
                    ALIGN_CENTER
                )

                logo.setPixmap(
                    pixmap.scaled(
                        260,
                        115,
                        KEEP_ASPECT,
                        SMOOTH_TRANSFORM
                    )
                )

                layout.addWidget(
                    logo
                )

            # Description.
            description = QLabel(
                "This QGIS plugin was generated with "
                "FjBa Plugin Generator V8.3 PRO.\n\n"
                "The QGIS action icon and FjBa brand logo "
                "are separate image assets.\n\n"
                "Supported generated-plugin windows can be "
                "automatically branded with the FjBa logo."
            )

            description.setAlignment(
                ALIGN_CENTER
            )

            description.setWordWrap(
                True
            )

            layout.addWidget(
                description
            )

            # Close button.
            close_button = QPushButton(
                "Close"
            )

            close_button.clicked.connect(
                dialog.accept
            )

            layout.addWidget(
                close_button
            )

            self.about_dialog = dialog

            if self.branding is not None:

                self.branding.brand_existing(
                    dialog
                )

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

        except Exception:

            log_exception(
                "Could not open About dialog"
            )

            QMessageBox.warning(
                self.iface.mainWindow(),
                "FjBa Plugin",
                "The About window could not be opened."
            )


# ============================================================
# QGIS PLUGIN FACTORY
# ============================================================

def classFactory(iface):
    """
    QGIS plugin entry point.

    QGIS calls this function when loading the plugin.
    """

    return FjBaGeneratedPlugin(iface)
