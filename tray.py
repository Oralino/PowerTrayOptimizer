import os
from PIL import Image, ImageDraw
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QImage, QAction
from PyQt6.QtCore import QObject, pyqtSignal
import win32gui
import win32ui
import win32con
import win32api

def create_status_icon(color_hex):
    image = Image.new('RGB', (16, 16), color=color_hex)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 15, 15], outline="black")
    
    data = image.tobytes("raw", "RGB")
    qimg = QImage(data, 16, 16, QImage.Format.Format_RGB888)
    return QIcon(QPixmap.fromImage(qimg))

def extract_exe_icon(exe_path):
    if not os.path.exists(exe_path):
        return None
    try:
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)

        hicon = None
        for i in range(4):
            large, small = win32gui.ExtractIconEx(exe_path, i)
            if small and small[0]:
                hicon = small[0]
                if large:
                    for h in large:
                        if h != hicon: win32gui.DestroyIcon(h)
                for h in small[1:]:
                    win32gui.DestroyIcon(h)
                break
            elif large and large[0]:
                hicon = large[0]
                for h in large[1:]:
                    win32gui.DestroyIcon(h)
                break

        if not hicon:
            return None

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)

        win32gui.DrawIconEx(
            hdc_mem.GetHandleOutput(), 0, 0, hicon, ico_x, ico_y, 0, None, win32con.DI_NORMAL
        )

        bmpinfo = hbmp.GetInfo()
        bmpbits = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGBA',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpbits, 'raw', 'BGRA', 0, 1
        )

        win32gui.DestroyIcon(hicon)

        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, bmpinfo['bmWidth'], bmpinfo['bmHeight'], QImage.Format.Format_RGBA8888)
        if qimg.isNull():
            return None
        return QIcon(QPixmap.fromImage(qimg))
    except Exception:
        return None

class TraySignalHandler(QObject):
    update_menu_signal = pyqtSignal()

class SystemTrayApp:
    def __init__(self, on_show_window, on_exit, on_launch_game, on_launch_launcher, power_manager):
        self.on_show_window = on_show_window
        self.on_exit = on_exit
        self.on_launch_game = on_launch_game
        self.on_launch_launcher = on_launch_launcher
        self.power_manager = power_manager

        self.signal_handler = TraySignalHandler()
        self.signal_handler.update_menu_signal.connect(self._build_menu_safely)

        self.green_icon = create_status_icon("#2E7D32")
        self.red_icon = create_status_icon("#D32F2F")

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.green_icon)
        self.tray.setToolTip("Power Plan: Balanced")

        self.menu = QMenu()
        self.apply_style()
        self._build_menu_safely()

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.handle_tray_activation)

    pyqt_double_click_reason = QSystemTrayIcon.ActivationReason.DoubleClick

    def handle_tray_activation(self, reason):
        if reason == self.pyqt_double_click_reason:
            self.on_show_window()

    def apply_style(self):
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E20;
                color: #E3E2E6;
                border: 1px solid #333538;
                padding: 4px 0px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #282A2C;
                color: #A8C7FA;
            }
            QMenu::icon {
                padding-left: 8px;
            }
            QMenu::separator {
                height: 1px;
                background: #333538;
                margin: 4px 0px;
            }
        """)

    def _build_menu_safely(self):
        self.menu.clear()

        for name, path in self.power_manager.games.items():
            game_icon = extract_exe_icon(path)
            action = QAction(name, self.menu)
            if game_icon and not game_icon.isNull():
                action.setIcon(game_icon)
            action.triggered.connect(lambda checked, g=name: self.on_launch_game(g))
            self.menu.addAction(action)

        if self.power_manager.games and self.power_manager.launchers:
            self.menu.addSeparator()

        for name, path in self.power_manager.launchers.items():
            launcher_icon = extract_exe_icon(path)
            action = QAction(f"{name}", self.menu)
            if launcher_icon and not launcher_icon.isNull():
                action.setIcon(launcher_icon)
            action.triggered.connect(lambda checked, l=name: self.on_launch_launcher(l))
            self.menu.addAction(action)

        if self.power_manager.games or self.power_manager.launchers:
            self.menu.addSeparator()

        library_action = QAction("Steam Library", self.menu)
        library_action.triggered.connect(lambda: os.startfile("steam://open/games"))
        self.menu.addAction(library_action)

        self.menu.addSeparator()

        show_action = QAction("Show Window", self.menu)
        show_action.triggered.connect(lambda: self.on_show_window())
        self.menu.addAction(show_action)

        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(lambda: self.on_exit())
        self.menu.addAction(exit_action)

    def update_menu(self):
        self.signal_handler.update_menu_signal.emit()

    def set_status(self, is_high_performance):
        if is_high_performance:
            self.tray.setIcon(self.red_icon)
            self.tray.setToolTip("Power Plan: High Performance")
        else:
            self.tray.setIcon(self.green_icon)
            self.tray.setToolTip("Power Plan: Balanced")

    def run(self):
        self.tray.show()

    def stop(self):
        self.tray.hide()