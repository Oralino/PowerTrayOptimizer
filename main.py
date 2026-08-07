import sys
import threading
import time
import psutil
from PyQt6.QtWidgets import QApplication

from power_manager import PowerManager
from gui import MainWindow
from tray import SystemTrayApp

def process_monitor_loop(pm, window, tray):
    while True:
        try:
            running = pm.is_game_running()
            if running != pm.is_active:
                pm.is_active = running
                if running:
                    pm.switch_power_plan(pm.high_perf_guid)
                    window.after(0, lambda: window.update_status_label(True))
                    if tray:
                        tray.set_status(True)
                else:
                    pm.switch_power_plan(pm.balanced_guid)
                    window.after(0, lambda: window.update_status_label(False))
                    if tray:
                        tray.set_status(False)
        except Exception:
            pass
        time.sleep(3)

def main():
    pm = PowerManager()

    window = MainWindow(pm, lambda: tray.update_menu())

    qapp = None
    tray = None

    def run_qt_tray():
        nonlocal qapp, tray
        qapp = QApplication(sys.argv)
        qapp.setQuitOnLastWindowClosed(False)

        def on_show_window():
            window.after(0, window.show_from_tray)

        def on_exit():
            tray.stop()
            window.after(0, window.destroy)
            qapp.quit()

        def on_launch_game(name):
            pm.launch_game(name)

        def on_launch_launcher(name):
            pm.launch_launcher(name)

        tray = SystemTrayApp(on_show_window, on_exit, on_launch_game, on_launch_launcher, pm)
        tray.run()
        qapp.exec()

    qt_thread = threading.Thread(target=run_qt_tray, daemon=True)
    qt_thread.start()

    def delayed_monitor_start():
        initial_check = pm.is_game_running()
        pm.is_active = initial_check
        if initial_check:
            window.update_status_label(True)
            if tray:
                tray.set_status(True)
        else:
            window.update_status_label(False)
            if tray:
                tray.set_status(False)

        monitor_thread = threading.Thread(target=process_monitor_loop, args=(pm, window, tray), daemon=True)
        monitor_thread.start()

    window.after(1000, delayed_monitor_start)

    window.mainloop()

if __name__ == "__main__":
    main()