import os
import re
import subprocess
import winreg
import psutil

CONFIG_FILE = os.path.join(os.environ["APPDATA"], "PowerTrayConfig.txt")
GAMES_FILE = os.path.join(os.environ["APPDATA"], "PowerTrayGames.txt")
LAUNCHERS_FILE = os.path.join(os.environ["APPDATA"], "PowerTrayLaunchers.txt")
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "PowerPlanManager"

class PowerManager:
    def __init__(self):
        self.games = {}
        self.launchers = {}
        self.is_active = False
        self.balanced_guid = None
        self.high_perf_guid = None
        self.load_config()
        self.load_games()
        self.load_launchers()

    def get_default_power_plans(self):
        output = subprocess.check_output("powercfg /l", shell=True).decode()
        high = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        bal = "381b4222-f694-41f0-9685-ff5bb260df2e"
        
        for line in output.splitlines():
            guid_match = re.search(r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})", line)
            if guid_match:
                guid = guid_match.group(1)
                if "high performance" in line.lower():
                    high = guid
                elif "balanced" in line.lower():
                    bal = guid
        return bal, high

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) >= 2:
                    self.balanced_guid, self.high_perf_guid = lines[0], lines[1]
        
        if not self.balanced_guid or not self.high_perf_guid:
            defaults = self.get_default_power_plans()
            self.balanced_guid = self.balanced_guid or defaults[0]
            self.high_perf_guid = self.high_perf_guid or defaults[1]

    def save_config(self, balanced, high_perf):
        self.balanced_guid = balanced
        self.high_perf_guid = high_perf
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"{balanced}\n{high_perf}\n")

    def load_games(self):
        if os.path.exists(GAMES_FILE):
            with open(GAMES_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    path = line.strip()
                    if path:
                        name = os.path.splitext(os.path.basename(path))[0]
                        self.games[name] = path

    def save_games(self):
        with open(GAMES_FILE, "w", encoding="utf-8") as f:
            for path in self.games.values():
                f.write(f"{path}\n")

    def load_launchers(self):
        if os.path.exists(LAUNCHERS_FILE):
            with open(LAUNCHERS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    path = line.strip()
                    if path:
                        parent_folder = os.path.basename(os.path.dirname(path))
                        file_name = os.path.splitext(os.path.basename(path))[0]
                        name = f"{parent_folder} ({file_name})" if parent_folder else file_name
                        self.launchers[name] = path

    def save_launchers(self):
        with open(LAUNCHERS_FILE, "w", encoding="utf-8") as f:
            for path in self.launchers.values():
                f.write(f"{path}\n")

    def add_game(self, path):
        if path.endswith(".exe"):
            name = os.path.splitext(os.path.basename(path))[0]
            if name not in self.games:
                self.games[name] = path
                self.save_games()
                return name
        return None

    def remove_game(self, name):
        if name in self.games:
            del self.games[name]
            self.save_games()

    def add_launcher(self, path):
        if path.endswith(".exe"):
            parent_folder = os.path.basename(os.path.dirname(path))
            file_name = os.path.splitext(os.path.basename(path))[0]
            name = f"{parent_folder} ({file_name})" if parent_folder else file_name
            if name not in self.launchers:
                self.launchers[name] = path
                self.save_launchers()
                return name
        return None

    def remove_launcher(self, name):
        if name in self.launchers:
            del self.launchers[name]
            self.save_launchers()

    def launch_game(self, name):
        if name not in self.games:
            return
        exe_path = self.games[name]
        if not os.path.exists(exe_path):
            return

        normalized_path = exe_path.replace("/", "\\").lower()

        if "steamapps\\common\\" in normalized_path:
            match = re.search(r"(?i)\\steamapps\\common\\([^\\]+)", normalized_path)
            if match:
                install_dir = match.group(1)
                steamapps_index = normalized_path.find("steamapps")
                steamapps_path = exe_path[:steamapps_index + 9]
                app_id = None

                if os.path.exists(steamapps_path):
                    for file in os.listdir(steamapps_path):
                        if file.startswith("appmanifest_") and file.endswith(".acf"):
                            manifest_path = os.path.join(steamapps_path, file)
                            try:
                                with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()
                                    if re.search(rf'"installdir"\s+"{re.escape(install_dir)}"', content, re.IGNORECASE):
                                        id_match = re.search(r"appmanifest_(\d+)\.acf", file)
                                        if id_match:
                                            app_id = id_match.group(1)
                                            break
                            except Exception:
                                pass

                if app_id:
                    os.startfile(f"steam://rungameid/{app_id}")
                    return

        working_dir = os.path.dirname(exe_path)
        try:
            subprocess.Popen([exe_path], cwd=working_dir)
        except OSError as e:
            if e.winerror == 740:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, None, working_dir, 1)
            else:
                raise

    def launch_launcher(self, name):
        if name not in self.launchers:
            return
        exe_path = self.launchers[name]
        if not os.path.exists(exe_path):
            return
        working_dir = os.path.dirname(exe_path)
        try:
            subprocess.Popen([exe_path], cwd=working_dir)
        except OSError as e:
            if e.winerror == 740:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, None, working_dir, 1)
            else:
                raise

    def is_game_running(self):
        running_processes = {p.info['name'].lower() for p in psutil.process_iter(['name'])}
        for game_name in self.games.keys():
            if f"{game_name.lower()}.exe" in running_processes:
                return True
        return False

    def switch_power_plan(self, guid):
        subprocess.run(f"powercfg /s {guid}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def is_startup_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, REG_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def set_startup(self, enable):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        if enable:
            exe_path = os.path.abspath(os.sys.executable)
            winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, REG_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)